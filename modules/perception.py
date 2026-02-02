import logging
from typing import Dict, Any, List
from modules.firmware.hal import SensorInterface, NetworkInterface

class PerceptionModule:
    """
    The Sensory Cortex of the Genesis OS.
    Interprets raw hardware and network data into actionable semantic information.
    """
    def __init__(self):
        self.logger = logging.getLogger('genesis.perception')
        self.hal_sensor = SensorInterface()
        self.hal_network = NetworkInterface()
        self.sensory_buffer = []

    def ingest_environment(self) -> Dict[str, Any]:
        """
        Scans the physical and digital environment for data points.
        """
        try:
            # Read from Hardware Abstraction Layer
            hardware_metrics = self.hal_sensor.read_sensors()
            network_metrics = self.hal_network.get_status()
            
            self.logger.info(f"Environment Scan Complete. CPU: {hardware_metrics['cpu']}%, Net: {network_metrics['status']}")
            return {
                "timestamp": self.hal_sensor.get_timestamp(),
                "hardware": hardware_metrics,
                "network": network_metrics
            }
        except Exception as e:
            self.logger.error(f"Perception Error: {e}")
            return {"error": str(e)}

    def interpret_signals(self, raw_data: Dict[str, Any]) -> List[str]:
        """
        Analyzes raw data to generate high-level signals/alerts.
        """
        signals = []
        
        # Heuristic analysis for CPU
        if raw_data['hardware']['cpu'] > 85:
            signals.append(f"CRITICAL_LOAD: CPU usage at {raw_data['hardware']['cpu']}%")
        elif raw_data['hardware']['cpu'] > 60:
            signals.append(f"WARNING_LOAD: CPU usage at {raw_data['hardware']['cpu']}%")

        # Heuristic analysis for Memory
        if raw_data['hardware']['memory']['available'] < 1024: # < 1GB
            signals.append("CRITICAL_LOW_MEM: Available memory below threshold")

        # Heuristic analysis for Network
        if raw_data['network']['latency'] > 200:
            signals.append(f"WARNING_LATENCY: Network latency at {raw_data['network']['latency']}ms")

        return signals

    def update_buffer(self, new_data: Dict[str, Any]):
        """Appends new data to the sensory buffer for temporal analysis."""
        self.sensory_buffer.append(new_data)
        # Keep buffer size manageable
        if len(self.sensory_buffer) > 100:
            self.sensory_buffer.pop(0)