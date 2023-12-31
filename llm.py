# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# Author: Thomas Roccia - @fr0gger_
# -------------------------------------------------------------------------
"""
LLM Provider using langchain
"""

from ..._version import VERSION
from ...common.utility import export
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool, initialize_agent, AgentType, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.prompts import MessagesPlaceholder

from msticpy.sectools.tilookup import TILookup
from msticpy.sectools.vtlookupv3 import VTLookupV3
from msticpy.context.tiproviders.riskiq import RiskIQ


# Important import to avoid the dataframe to be truncated and avoid the LLM to retrieve the content
import pandas as pd

pd.set_option("display.max_colwidth", None)


__version__ = VERSION
__author__ = "Thomas Roccia | @fr0gger_"


#########################################################################
# TODO: Add a function that will allow to retrieve the desired API key from the msticpyconfig.yaml file
# llm = OpenAI(openai_api_key="...")
llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)

#########################################################################
# Alternatively, open-source LLM hosted on Hugging Face
# pip install huggingface_hub
# from langchain import HuggingFaceHub
# llm = HuggingFaceHub(repo_id = "google/flan-t5-xl")



class VTAgent:
    """VTAgent leverages the VirusTotal API to retrieve threat information."""
    
    def __init__(self):
         """Initialize TILookup."""
         self.vt_lookup = VTLookupV3()

    def parsing_parameter1(self, string):
        """Parse the action_input from the LLM to retrieve the observable, observable_type"""
        observable, observable_type = string.split(",")
        return self.url_ip_domain_info(observable, observable_type)

    def url_ip_domain_info(self, observable: str, type) -> str:
        """Get information about a given url."""
        result = self.vt_lookup.lookup_ioc(observable=observable, vt_type=type)
        return str(result)[:3500]

    def samples_info(self, hash: str) -> str:
        """Get information about a given sample based on its hash."""
        result = self.vt_lookup.get_object(hash, "file")
        return str(result)[:3500]
    
    def parsing_parameter(self, string):
        """Parse the action_input from the LLM to retrieve the observable, observable_type and relationship."""
        observable, observable_type, relationship = string.split(",")
        return self.get_relationships(observable, observable_type, relationship)

    def get_relationships(self, observable: str, observable_type: str, relationship: str) -> str:
        """Retrieve relationship with a given observable."""
        result = self.vt_lookup.lookup_ioc_relationships(observable=observable, vt_type=observable_type, relationship=relationship, limit="10")
        return result

    def get_tools(self):
        """Return the list of tools available for this agent."""
        return [
            Tool(
                name="Retrieve_url_ip_domain_Info",
                func=self.parsing_parameter1,
                description="Useful when you need to look up threat intelligence information for an url, ip or a domain. if it is an ip, the observable_type should be 'ip_address', if it is a domain, the observable_type should be 'domain' and if it is an url, the observable_type should be 'url'. The input to this tool should be a comma separated list that contains an observable (IP or domain, or url) and observable_type that can be 'ip_address', 'domain' or 'url'. For example, 8.8.8.8,ip_address would be the input to retrieve the info about the ip 8.8.8.8 ",
            ),
            Tool(
                name="Retrieve_Sample_information",
                func=self.samples_info,
                description="Useful when you need to obtain more details about a sample. A sample must be specified by its hash.",
            ),
            Tool(
                name="Retrieve_Sample_Relationships",
                func=self.parsing_parameter,
                description="Useful when you need to get communicating_samples or donwloaded_samples from an IP, an url or a domain. The input to this tool should be a comma separated list that contains an observable (IP or domain, or url) and observable_type that can be 'ip_address', 'domain' or 'url' and the relationship that can be 'communicating_files' or 'downloaded_files'. For example, 8.8.8.8,ip_address,communicating_files would be the input to retrieve the communicating files from 8.8.8.8",
            ),
        ]


class AbuseIPDBAgent:
    """
    AbuseIPDB agent mapping to AbuseIPDB TIProvider
    https://github.com/microsoft/msticpy/blob/main/msticpy/context/tiproviders/abuseipdb.py
    """

    def __init__(self):
        # Initialize your Agent from MSTICpy
        self.ti_lookup = TILookup()

    def ip_info(self, ip_address: str) -> str:
        """Get information about a given IP address."""
        result = self.ti_lookup.lookup_ioc(
            observable=ip_address,
            ioc_type="ipv4",
            ioc_query_type="full",
            providers=["AbuseIPDB"],
        )
        return str(result)[:3500]

    def get_tools(self):
        return [
            Tool(
                name="Retrieve_IP_Info",
                func=self.ip_info,
                description="Useful when you need to look up threat intelligence information for an IP address.",
            )
        ]


class GreyNoiseAgent:
    """
    GreyNoise agent mapping to GreyNoise TIProvider
    https://github.com/microsoft/msticpy/blob/main/msticpy/context/tiproviders/greynoise.py
    """

    def __init__(self):
        # Initialize your Agent from MSTICpy
        self.ti_lookup = TILookup()

    def ip_info(self, ip_address: str) -> str:
        """Get information about a given IP address."""
        result = self.ti_lookup.lookup_ioc(
            observable=ip_address,
            ioc_type="ipv4",
            ioc_query_type="full",
            providers=["GreyNoise"],
        )
        return str(result)[:3500]

    def get_tools(self):
        return [
            Tool(
                name="Retrieve_IP_greynoise_Info",
                func=self.ip_info,
                description="Useful when you need to look up threat intelligence information for an IP address.",
            )
        ]


class OTXAgent:
    """
    OTX agent mapping to OTX TIProvider
    https://github.com/microsoft/msticpy/blob/main/msticpy/context/tiproviders/alienvault_otx.py
    """

    def __init__(self):
        # Initialize your Agent from MSTICpy
        self.ti_lookup = TILookup()

    def ip_info(self, ip_address: str) -> str:
        """Get information about a given IP address.
        FIXME! differentiate ioc_type ipv4, ipv6, -passivedns, -geo
        """
        result = self.ti_lookup.lookup_ioc(
            observable=ip_address,
            ioc_type="ipv4",
            ioc_query_type="full",
            providers=["OTX"],
        )
        return str(result)[:3500]

    def domain_info(self, domain: str) -> str:
        """Get information about a given domain."""
        result = self.ti_lookup.lookup_ioc(
            observable=domain, ioc_type="dns", providers=["OTX"]
        )
        return str(result)[:3500]

    def url_info(self, url: str) -> str:
        """Get information about a given url."""
        result = self.ti_lookup.lookup_ioc(
            observable=url, ioc_type="url", providers=["OTX"]
        )
        return str(result)[:3500]

    def samples_info(self, hash: str) -> str:
        """Get information about a given sample based on its hash."""
        return self.ti_lookup.lookup_ioc(
            observable=hash, ioc_type="file_hash", providers=["OTX"]
        )[:3500]

    def get_tools(self):
        return [
            Tool(
                name="Retrieve_IP_OTX_Info",
                func=self.ip_info,
                description="Useful when you need to look up threat intelligence information for an IP address.",
            ),
            Tool(
                name="Retrieve_Domain_OTX_Info",
                func=self.domain_info,
                description="Useful when you need to look up threat intelligence information for a domain.",
            ),
            Tool(
                name="Retrieve_url_OTX_Info",
                func=self.url_info,
                description="Useful when you need to look up threat intelligence information for an url.",
            ),
            Tool(
                name="Retrieve_Sample_OTX_information",
                func=self.samples_info,
                description="Useful when you need to obtain more details about a sample.",
            ),
        ]

# Might make sense to combine all TI Lookup methods in one Agent with TILookup class

class RiskIQAgent:
    """RiskIQAgent leverages RiskIQ API to retrieve threat information"""

    def __init__(self):
        """Initialize RiskIQ class"""
        self.risk_iq_lookup = RiskIQ()

    def ip_info(self, ip_address: str) -> str:
        """Get information about a given IP address."""
        result = self.risk_iq_lookup.lookup_ioc(ioc=ip_address, ioc_type='ipv4')
        return str(result)[:3500]

    def domain_info(self, domain: str) -> str:
        """Get information about a given domain."""
        result = self.risk_iq_lookup.lookup_ioc(ioc=domain, ioc_type='dns')
        return str(result)[:3500]

    def get_tools(self):
            """Return the list of tools available for this agent."""
            return [

                Tool(
                    name='Retrieve_IP_Info',
                    func=self.ip_info,
                    description="Useful when you need to look up threat intelligence information for an IP address."
                ),
                Tool(
                    name='Retrieve_Domain_Info',
                    func=self.domain_info,
                    description="Useful when you need to look up threat intelligence information for a domain or a hostname."
                )
            ]

class AgentRunner:  # Replace with your actual class name
    _agent_initialized = False
    _agent = None  # To store the initialized agent instance

    AGENTS = {
        "VTAgent": VTAgent(),
        "AbuseIPDBAgent": AbuseIPDBAgent(),
        "GreyNoiseAgent": GreyNoiseAgent(),
        "OTXAgent": OTXAgent(),
        "RiskIQAgent": RiskIQAgent(),
        # "SkeletonAgent": SkeletonAgent()
        # Add other agents here like: "OtherAgent": OtherAgent()
    }

    @classmethod
    def initialize_agent(cls, agent_name: str, debug=True):
        if agent_name not in cls.AGENTS:
            raise ValueError(f"Agent '{agent_name}' not found. Available agents are: {', '.join(cls.AGENTS.keys())}")

        selected_agent = cls.AGENTS[agent_name]
        tools = selected_agent.get_tools()
        
        if not cls._agent_initialized:

            memory = ConversationBufferMemory(memory_key="chat_history")

            cls._agent = initialize_agent(tools, llm=llm, memory=memory, agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION, verbose=debug)
            cls._agent_initialized = True

    @classmethod
    def run_agent(cls, agent_name: str, prompt: str, debug=False):
        if not cls._agent_initialized:
            cls.initialize_agent(agent_name, debug=debug)
        
        if cls._agent:
            cls._agent.run(input=prompt)
            print(cls._agent.memory.buffer)