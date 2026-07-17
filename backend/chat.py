from dotenv import load_dotenv
from agents.ceo.agent import CEOAgent

load_dotenv()

ceo = CEOAgent()

print("\nPersonal Life Manager")
print("---------------------")
print("Type 'quit' to exit\n")

while True:
    user_input = input("You: ").strip()
    if not user_input:
        continue
    if user_input.lower() == "quit":
        break
    response = ceo.chat(user_input)
    print(f"\nAssistant: {response}\n")
