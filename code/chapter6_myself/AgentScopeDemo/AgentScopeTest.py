from agentscope.agent import AgentBase
from agentscope.message import Msg

class CustomAgent(AgentBase):
    def __init__(self,name: str, **kwargs):
        super().__init__(name, **kwargs)

    def reply(self, x: Msg) -> Msg:
        response =  self.model(x.content)
        return Msg(name=self.name, content=response, role="assistant")
    
    def observe(self, x: Msg) -> None:
        self.memory.add(x)