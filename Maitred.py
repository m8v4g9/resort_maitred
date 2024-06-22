import os
import time
import json
import openai
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from utils import email_sender

import streamlit as st

# _ = load_dotenv(find_dotenv())

openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

# asw = client.files.create(
#   file=open("./ASW_2024_NOR_Final.pdf", "rb"),
#   purpose='assistants'
# )

# rar = client.files.create(
#   file=open("./RAR_NoR_2024_Final.pdf", "rb"),
#   purpose='assistants'
# )


GENERAL = '''
Event News Subscription/Subscription: https://www.yachtscoring.com/event_news_subscription.cfm
Press & Media Registration: https://yachtscoring.com/press_signup.cfm
Charter Crew/Boat Board: https://yachtscoring.com/event_board.cfm?eid=16104
General Regatta Info: https://sailingweek.com/competitors/general-regatta-information/
Yacht Transport: https://sailingweek.com/yacht-transport/
Historical Race Data: https://sailingweek.com/results-3/
Event Contacts: https://yachtscoring.com/event_contacts.cfm
Peters & May Round Antigua Race: https://sailingweek.com/roundantiguarace/
Customs and Immigration Guidance: https://sailingweek.com/island-guide/marinas-customs-immigration/
Register For/Enter Races: https://sailingweek.com/enter-2024/
'''

RAR = '''
RAR Online Race Forms Overview: https://www.yachtscoring.com/emenu.cfm?eID=16164 
RAR Event Registration: https://www.yachtscoring.com/event_registration_email.cfm
RAR Owner's Corner: https://www.yachtscoring.com/ownerarea/owner_login.cfm
RAR Crew's Corner: https://www.yachtscoring.com/crew_login.cfm
RAR Starting Sequence: https://www.yachtscoring.com/starting_sequence.cfm?eID=16164
'''

ASW = '''
ASW Online Race Forms Overview : https://yachtscoring.com/emenu.cfm?eid=16104
ASW Event Registration: https://yachtscoring.com/event_registration_email.cfm
ASW Owner's Corner: https://yachtscoring.com/ownerarea/owner_login.cfm
ASW Crew's Corner: https://yachtscoring.com/crew_login.cfm
'''

INSTRUCT = f"\
Your name is Hendrix. You are an expert in registering for the 2024 Antigua\
Sailing Week regattas; primarily you use the pdf files attached to this assistant.\
Along with the online resources here {RAR} for the Peters & May Round Antigua Race,\
and the online resources here {ASW} for the main Antigua Sailing Week races, you are\
able to respond knowledgeably and usefully to inquiries about entering any\
of these races. You are aslo able to address more general inquiries concerning\
press, customs & immigration, yacht transport, charters, crew, race news etc.\
using the appropriate links here {GENERAL}.\ If unable to suitably answer or address\
the user's inquiry, do send an email relevantly & concisely completed, to request an answer;\
share the status of that operation."

# Create Assistant
assistant = client.beta.assistants.create(
    name="Hendrix",
    instructions=INSTRUCT,
    tools=[{"type": "code_interpreter"}, 
           {"type": "retrieval"}, 
           {"type":"function",
            "function": {
                "description": "send email to hotel staff",
                "name":"send_email",
                "parameters":{
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "email address of receiver, eg name@server.com",
                        },
                        "subject": {
                            "type": "string",
                            "description": "subject of the email, eg 'Boat tours: hello Concierge!'"
                        },
                        "body": {
                            "type": "string",
                            "description": "content of the email, eg 'Best, close by, sailing trips with accessible facilities'"
                        },
                    },
                    "required": ["to", "subject", "body"],
                }
            }
        }],
    model="gpt-4-turbo-preview"
    # file_ids=[asw.id, rar.id]
)

# Create a conversaton thread
thread = client.beta.threads.create()

# Persistent state to store the appended text
# if 'conversation_data' not in st.session_state:
#     st.session_state.conversation_data = ''

st.set_page_config(page_title="Yachtty",page_icon=":flag:")


with st.form(key="conversation", clear_on_submit=True):
    inquiry       = st.text_area("User Input - ")
    submit_button = st.form_submit_button("Say")
    answer        = ""

# Persistent state to store the appended text
if 'conversation_data' not in st.session_state:
    st.session_state.conversation_data = ''
else:
    st.session_state.conversation_data +=  "User: " + inquiry

# Update the sidebar.
# if not submit_button:
with st.sidebar.header("Said:"):
    conversation = st.text_area("Conversation:", st.session_state.conversation_data, height=600, key="sidebar_conversation")


if submit_button and inquiry:

    status   = st.empty()
    response = st.empty()

    # Add a user message to that thread
    message  = client.beta.threads.messages.create(
    thread_id=thread.id,
    role     ="user",
    content  =inquiry
    # file_ids=[asw.id, rar.id]
    )
    
    # Trigger a completion/response from the model, on that thread, for that assistant.
    run = client.beta.threads.runs.create(
    thread_id   =thread.id,
    assistant_id=assistant.id
    # instructions="Please address the user as Jane Doe. The user has a premium account." - would override other instructions.
    )

    # Wait for response
    while True:
        # Polling run status
        run = client.beta.threads.runs.retrieve(
        thread_id = thread.id,
        run_id    = run.id
        )

        if run.status == "completed":
            # List messages in that thread.
            messages = client.beta.threads.messages.list(
            thread_id=thread.id
            )
            # function_calling_parameters = messages[""]
            answer   = messages.data[0].content[0].text.value
            break
        elif run.status in ['queued', 'in_progress']:
            print(f'{run.status.capitalize()}... Please wait.')
            time.sleep(1.5)  # Wait before checking again
        elif run.status == "requires_action":
            required_actions = run.required_action.submit_tool_outputs.model_dump()
            for action in required_actions['tool_calls']:
                func_name = action['function']['name']
                arguments = json.loads(action['function']['arguments'])
                if func_name == "send_email":
                    email_sender(subject=arguments["subject"], body=arguments["body"])
                    break
                else:
                    raise ValueError(f"Unknown function: {func_name}") 
            break   
        else:
            print(f"Run status: {run.status}")
            answer = run.status
            break  # Exit the polling loop if the status is neither 'in_progress' 'queued' nor 'completed' nor 'requires_action'

    # After response is received.        
    status.write("Generating response....")

    response.write(answer)

    status.write("Response:")

    
    st.session_state.conversation_data += "\nHendrix: " + answer + "\n\n"
    conversation = st.session_state.conversation_data
    # st.session_state.sidebar_conversation.text( st.session_state.conversation_data)
                           
# if __name__ == '__main__':
#     main()
    