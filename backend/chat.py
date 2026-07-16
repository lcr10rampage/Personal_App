import os
from dotenv import load_dotenv
from agents.ceo import run_ceo

load_dotenv()

history = []

print("\nPersonal Life Manager")
print("---------------------")
print("Type 'quit' to exit\n")

while True:
    user_input = input("You: ").strip()
    if not user_input:
        continue
    if user_input.lower() == "quit":
        break

    response = run_ceo(user_input, history)
    print(f"\nAssistant: {response}\n")

    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": response})
