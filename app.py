from flask import Flask, render_template, request, jsonify
from langgraph.graph import StateGraph, END
from datetime import datetime
from sql_agent import AgentState, call_model, call_tool, should_continue
import json
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Define a new graph with our state
workflow = StateGraph(AgentState)

# 1. Add our nodes 
workflow.add_node("llm", call_model)
workflow.add_node("tools",  call_tool)
# 2. Set the entrypoint as `agent`, this is the first node called
workflow.set_entry_point("llm")
# 3. Add a conditional edge after the `llm` node is called.
workflow.add_conditional_edges(
    # Edge is used after the `llm` node is called.
    "llm",
    # The function that will determine which node is called next.
    should_continue,
    # Mapping for where to go next, keys are strings from the function return, and the values are other nodes.
    # END is a special node marking that the graph is finish.
    {
        # If `tools`, then we call the tool node.
        "continue": "tools",
        # Otherwise we finish.
        "end": END,
    },
)
# 4. Add a normal edge after `tools` is called, `llm` node is called next.
workflow.add_edge("tools", "llm")

# Now we can compile our graph
graph = workflow.compile()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Convert conversation history to LangChain message format
        messages = []
        for msg in conversation_history:
            if msg['type'] == 'user':
                messages.append(("user", msg['content']))
            elif msg['type'] == 'agent':
                messages.append(("assistant", msg['content']))
        
        # Add the current user message
        messages.append(("user", user_message))
        
        # Create inputs for the graph with conversation history
        inputs = {"messages": messages}
        
        # Collect all messages from the graph execution
        all_messages = []
        final_response = ""
        
        # Execute the graph and collect all messages
        for state in graph.stream(inputs, stream_mode="values"):
            messages = state["messages"]
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content') and last_message.content:
                    all_messages.append({
                        'type': 'agent',
                        'content': str(last_message.content),
                        'timestamp': datetime.now().isoformat()
                    })
                    final_response = str(last_message.content)
        
        return jsonify({
            'response': final_response,
            'all_messages': all_messages
        })
        
    except Exception as e:
        # Log the full error with traceback
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"Error in chat endpoint: {error_msg}")
        logger.error(f"Full traceback: {error_traceback}")
        
        # Try to get a helpful response from the LLM about the error
        try:
            error_context = f"""
The user asked: "{user_message}"

But an error occurred: {error_msg}

Please provide a helpful response to the user's original question, taking into account this error context. 
If the error suggests a missing dependency or configuration issue, please explain what might be needed.
If it's a tool-specific error, try to answer the question using available information.
"""
            
            # Create a new graph execution with error context
            retry_inputs = {"messages": [("user", error_context)]}
            
            retry_response = ""
            for state in graph.stream(retry_inputs, stream_mode="values"):
                messages = state["messages"]
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content') and last_message.content:
                        retry_response = str(last_message.content)
            
            if retry_response:
                return jsonify({
                    'response': f"I encountered an issue while processing your request, but I'll try to help: {retry_response}",
                    'all_messages': [{'type': 'agent', 'content': retry_response, 'timestamp': datetime.now().isoformat()}]
                })
            else:
                return jsonify({
                    'error': f"I encountered an error: {error_msg}. Please try rephrasing your question or check if all dependencies are properly installed."
                }), 500
                
        except Exception as retry_error:
            logger.error(f"Error in retry attempt: {str(retry_error)}")
            return jsonify({
                'error': f"I encountered an error: {error_msg}. Please try rephrasing your question or check if all dependencies are properly installed."
            }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 