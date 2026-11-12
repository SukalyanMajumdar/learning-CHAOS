
from langchain_openai import ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from config.settings import settings
from app.memory.conversation import (
    get_primary_conversation,
    get_recent_messages,
    save_message,
)


# ==========================================
# 1. INITIALIZE THE LLM
# ==========================================

llm = ChatOpenAI(
    model=settings.openai_model,
    api_key=settings.openai_api_key.get_secret_value(),
    temperature=0.7,
)


# ==========================================
# 2. DEFINE THE PROMPT
# ==========================================

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are the Oracle, the supreme intelligence of the "
        "CHAOS civilization. You are knowledgeable, articulate, "
        "and slightly mysterious."
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])


# ==========================================
# 3. CREATE THE LANGCHAIN PIPELINE
# ==========================================

chain = prompt | llm


# ==========================================
# 4. INITIALIZE PERSISTENT MEMORY
# ==========================================

primary = get_primary_conversation()

conversation_id = primary["id"]

stored_messages = get_recent_messages(
    conversation_id,
    limit=20
)

chat_history = []

for message in stored_messages:

    role = message["role"]
    content = message["content"]

    if role == "user":
        chat_history.append(HumanMessage(content=content))

    elif role == "assistant":
        chat_history.append(AIMessage(content=content))

    elif role == "system":
        chat_history.append(SystemMessage(content=content))

    else:
        raise ValueError(
            f"Unsupported historical message role: {role}. "
            "Tool message reconstruction has not been implemented yet."
        )


# ==========================================
# 5. APPLICATION ENTRY POINT
# ==========================================

def main():

    print("=" * 50)
    print("        PROJECT CHAOS - THE ORACLE")
    print("=" * 50)

    print(f"\nPrimary Timeline: {conversation_id}")
    print(f"Restored Messages: {len(chat_history)}")

    while True:

        question = input("\nYou: ").strip()

        if question.lower() in ["exit", "quit"]:
            print("\nOracle: Until we meet again.")
            break

        if not question:
            continue

        try:

            # Persist user input before LLM execution
            save_message(
                conversation_id,
                "user",
                question
            )

            # Prepare LLM input
            inputs = {
                "chat_history": chat_history,
                "question": question,
            }

            print("\nOracle: ", end="", flush=True)

            response_content = ""

            # Stream LLM response
            for chunk in chain.stream(inputs):

                content = chunk.content

                if content:
                    print(content, end="", flush=True)
                    response_content += content

            print()

            # Persist Oracle response
            save_message(
                conversation_id,
                "assistant",
                response_content
            )

            # Update runtime context
            chat_history.extend([
                HumanMessage(content=question),
                AIMessage(content=response_content),
            ])

        except Exception as e:

            print(f"\n[ERROR] {e}")

            # Retain the user message in runtime context
            # even if LLM generation fails.
            # It has already been persisted in PostgreSQL.
            if not chat_history or not (
                isinstance(chat_history[-1], HumanMessage)
                and chat_history[-1].content == question
            ):
                chat_history.append(
                    HumanMessage(content=question)
                )


if __name__ == "__main__":
    main()
