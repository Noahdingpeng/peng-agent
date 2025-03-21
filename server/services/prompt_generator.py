from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

def memory_message_chain(human_input, ai_response):
    return [HumanMessage(content=human_input), AIMessage(content=ai_response)]

def humen_message_chain(human_input):
    return ("human", human_input)

def rag_prompt_template():
    return ChatPromptTemplate.from_messages([
        ("system", "Answer any use questions based solely on the context below:\n\n<context>\n{context}\n</context>"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}")
    ])
