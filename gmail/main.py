from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# from gemini_functions_agent import agent_executor as gemini_functions_agent_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import hub
from langchain.agents import AgentType, initialize_agent
credentials = get_gmail_credentials(
    token_file=os.path.abspath(os.path.join(os.path.dirname(__file__), 'token.json')),
    scopes=["https://mail.google.com/"],
    client_secrets_file=os.path.abspath(os.path.join(os.path.dirname(__file__), 'credentials.json')),
)
api_resource = build_resource_service(credentials=credentials)
toolkit = GmailToolkit(api_resource=api_resource)

tools = toolkit.get_tools()
print(tools)


llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash",
                             verbose=True,
                             temperature=0.5,
                             google_api_key=os.getenv("GOOGLE_API_KEY"))

agent = initialize_agent(
    tools=toolkit.get_tools(),
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)


agent.invoke(
    {
        "input":"""send a mial seperately  to danieldask062@gmail.com and 221501022@rajalakshmi.edu.in i love you"""
    }
)