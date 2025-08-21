"""
Context variables for global state management.

Uses ContextVar to avoid prop drilling and maintain clean function signatures.
"""

from enum import Enum
from typing import Optional

from adbutils import AdbClient
from openai import BaseModel
from pydantic import ConfigDict
from typing_extensions import Literal

from mobile_use.clients.device_hardware_client import DeviceHardwareClient
from mobile_use.clients.screen_api_client import ScreenApiClient


class DevicePlatform(str, Enum):
    """Mobile device platform enumeration."""

    ANDROID = "android"
    IOS = "ios"


class DeviceContext(BaseModel):
    host_platform: Literal["WINDOWS", "LINUX"]
    mobile_platform: DevicePlatform
    device_id: str
    device_width: int
    device_height: int

    def to_str(self):
        return (
            f"Host platform: {self.host_platform}\n"
            f"Mobile platform: {self.mobile_platform.value}\n"
            f"Device ID: {self.device_id}\n"
            f"Device width: {self.device_width}\n"
            f"Device height: {self.device_height}\n"
        )


# only contains the trace id for now. may contain other things later
class ExecutionSetup(BaseModel):
    trace_id: str


class MobileUseContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    device: DeviceContext
    hw_bridge_client: DeviceHardwareClient
    screen_api_client: ScreenApiClient
    adb_client: Optional[AdbClient] = None
    execution_setup: Optional[ExecutionSetup] = None

    def get_adb_client(self) -> AdbClient:
        if self.adb_client is None:
            raise ValueError("No ADB client in context.")
        return self.adb_client  # type: ignore
