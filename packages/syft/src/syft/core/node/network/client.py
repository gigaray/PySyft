# stdlib
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

# third party
from nacl.signing import SigningKey
from nacl.signing import VerifyKey
from pandas import DataFrame
from typing_extensions import final

# relative
from ....logger import traceback_and_raise
from ...common.message import SyftMessage
from ...common.uid import UID
from ...io.location import Location
from ...io.location import SpecificLocation
from ...io.route import Route
from ..common.action.exception_action import ExceptionMessage
from ..common.client import Client
from ..common.client_manager.association_api import AssociationRequestAPI
from ..common.client_manager.dataset_api import DatasetRequestAPI
from ..common.client_manager.role_api import RoleRequestAPI
from ..common.client_manager.user_api import UserRequestAPI
from ..common.client_manager.vpn_api import VPNAPI
from ..common.node_service.network_search.network_search_messages import (
    NetworkSearchMessage,
)
from ..domain.enums import RequestAPIFields


@final
class NetworkClient(Client):

    network: SpecificLocation  # redefine the type of self.vm to not be optional

    def __init__(
        self,
        name: Optional[str],
        routes: List[Route],
        network: SpecificLocation,
        domain: Optional[Location] = None,
        device: Optional[Location] = None,
        vm: Optional[Location] = None,
        signing_key: Optional[SigningKey] = None,
        verify_key: Optional[VerifyKey] = None,
    ):
        super().__init__(
            name=name,
            routes=routes,
            network=network,
            domain=domain,
            device=device,
            vm=vm,
            signing_key=signing_key,
            verify_key=verify_key,
        )

        self.users = UserRequestAPI(client=self)
        self.roles = RoleRequestAPI(client=self)
        self.association = AssociationRequestAPI(client=self)
        self.datasets = DatasetRequestAPI(client=self)

        self.post_init()

        self.vpn = VPNAPI(client=self)

    @property
    def id(self) -> UID:
        return self.network.id

    @property
    def domain(self) -> Optional[Location]:
        """This client points to a node, if that node lives within a domain
        or is a domain itself, this property will return the Location of that domain
        if it is known by the client."""

        return super().domain

    @domain.setter
    def domain(self, new_domain: Location) -> Optional[Location]:
        """This client points to a node, if that node lives within a domain
        or is a domain itself and we learn the Location of that domain, this setter
        allows us to save the Location of that domain for use later. We use a getter
        (@property) and setter (@set) explicitly because we want all clients
        to efficiently save an address object for use when sending messages to their
        target. That address object will include this information if it is available"""

        traceback_and_raise(
            Exception(
                "This client points to a network, you don't need a Domain Location."
            )
        )

    @property
    def device(self) -> Optional[Location]:
        """This client points to a node, if that node lives within a device
        or is a device itself, this property will return the Location of that device
        if it is known by the client."""

        return super().device

    @device.setter
    def device(self, new_device: Location) -> Optional[Location]:
        """This client points to a node, if that node lives within a device
        or is a device itself and we learn the Location of that device, this setter
        allows us to save the Location of that device for use later. We use a getter
        (@property) and setter (@set) explicitly because we want all clients
        to efficiently save an address object for use when sending messages to their
        target. That address object will include this information if it is available"""

        traceback_and_raise(
            Exception(
                "This client points to a network, you don't need a Device Location."
            )
        )

    @property
    def vm(self) -> Optional[Location]:
        """This client points to a node, if that node lives within a vm
        or is a vm itself, this property will return the Location of that vm
        if it is known by the client."""

        return super().vm

    @vm.setter
    def vm(self, new_vm: Location) -> Optional[Location]:
        """This client points to a node, if that node lives within a vm
        or is a vm itself and we learn the Location of that vm, this setter
        allows us to save the Location of that vm for use later. We use a getter
        (@property) and setter (@set) explicitly because we want all clients
        to efficiently save an address object for use when sending messages to their
        target. That address object will include this information if it is available"""

        traceback_and_raise(
            Exception("This client points to a network, you don't need a VM Location.")
        )

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {self.name}>"

    def join_network(self, host_or_ip: str) -> None:
        return self.vpn.join_network(host_or_ip=host_or_ip)

    def vpn_status(self) -> Dict[str, Any]:
        return self.vpn.get_status()

    def search(self, query: List, pandas: bool = False) -> Any:
        response = self._perform_grid_request(
            grid_msg=NetworkSearchMessage, content={"content": query}
        )
        if pandas:
            response = DataFrame(response)

        return response

    def _perform_grid_request(
        self, grid_msg: Any, content: Optional[Dict[Any, Any]] = None
    ) -> SyftMessage:
        if content is None:
            content = {}
        # Build Syft Message
        content[RequestAPIFields.ADDRESS] = self.address
        content[RequestAPIFields.REPLY_TO] = self.address
        signed_msg = grid_msg(**content).sign(signing_key=self.signing_key)
        # Send to the dest
        response = self.send_immediate_msg_with_reply(msg=signed_msg)
        if isinstance(response, ExceptionMessage):
            raise response.exception_type
        else:
            return response
