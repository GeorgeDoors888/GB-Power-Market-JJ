#!/usr/bin/env python3
"""
IRIS Message Client - Azure Service Bus Consumer
Downloads BMRS IRIS messages and saves to local JSON files
"""

import os
import json
import logging
import ast
from datetime import datetime
from pathlib import Path
from dacite import from_dict
from azure.servicebus import ServiceBusClient, ServiceBusReceivedMessage
from azure.identity import ClientSecretCredential, InteractiveBrowserCredential
from azure.servicebus.exceptions import ServiceBusError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/iris-pipeline/logs/iris_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IrisClient:
    """Downloads IRIS messages from Azure Service Bus"""
    
    def __init__(self, config_path='config.json'):
        """Initialize client with configuration"""
        self.config = self._load_config(config_path)
        self.output_dir = Path(self.config.get('output_dir', '/opt/iris-pipeline/data'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config: {e}")
            raise
    
    def connect(self):
        """Establish connection to Azure Service Bus"""
        try:
            connection_str = self.config['azure']['connection_string']
            self.client = ServiceBusClient.from_connection_string(connection_str)
            logger.info("Connected to Azure Service Bus")
        except KeyError:
            logger.error("Missing 'azure.connection_string' in config")
            raise
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def download_messages(self, queue_name, max_messages=100, max_wait_seconds=60):
        """
        Download messages from specified queue
        
        Args:
            queue_name: Azure Service Bus queue name
            max_messages: Maximum messages to download per batch
            max_wait_seconds: Maximum time to wait for messages
        """
        try:
            receiver = self.client.get_queue_receiver(queue_name=queue_name)
            messages_downloaded = 0
            
            logger.info(f"Listening on queue: {queue_name}")
            
            with receiver:
                received_msgs = receiver.receive_messages(
                    max_message_count=max_messages,
                    max_wait_time=max_wait_seconds
                )
                
                for msg in received_msgs:
                    try:
                        # Parse message body
                        message_data = json.loads(str(msg))
                        
                        # Extract report type and timestamp
                        report_type = message_data.get('reportType', 'UNKNOWN')
                        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                        
                        # Save to file
                        filename = f"{report_type}_{timestamp}_{msg.message_id}.json"
                        filepath = self.output_dir / filename
                        
                        with open(filepath, 'w') as f:
                            json.dump(message_data, f, indent=2)
                        
                        # Complete the message (remove from queue)
                        receiver.complete_message(msg)
                        
                        messages_downloaded += 1
                        logger.info(f"Downloaded: {filename}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in message: {e}")
                        receiver.dead_letter_message(msg, reason="Invalid JSON")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        receiver.abandon_message(msg)
            
            logger.info(f"Downloaded {messages_downloaded} messages from {queue_name}")
            return messages_downloaded
            
        except Exception as e:
            logger.error(f"Error downloading messages: {e}")
            raise
    
    def download_all_queues(self):
        """Download messages from all configured queues"""
        total_downloaded = 0
        
        for queue_config in self.config.get('queues', []):
            queue_name = queue_config['name']
            max_messages = queue_config.get('max_messages', 100)
            
            try:
                count = self.download_messages(
                    queue_name=queue_name,
                    max_messages=max_messages
                )
                total_downloaded += count
            except Exception as e:
                logger.error(f"Failed to download from {queue_name}: {e}")
        
        return total_downloaded
    
    def cleanup_old_files(self, hours=48):
        """Delete files older than specified hours"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=hours)
        deleted = 0
        
        for filepath in self.output_dir.glob('*.json'):
            if datetime.fromtimestamp(filepath.stat().st_mtime) < cutoff:
                filepath.unlink()
                deleted += 1
                logger.debug(f"Deleted old file: {filepath.name}")
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old files")
        
        return deleted
    
    def close(self):
        """Close connection to Azure Service Bus"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("Disconnected from Azure Service Bus")


def main():
    """Main entry point"""
    import sys
    
    # Get config path from command line or use default
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    
    # Initialize client
    client = IrisClient(config_path)
    
    try:
        # Connect to Azure
        client.connect()
        
        # Download messages
        total = client.download_all_queues()
        logger.info(f"Total messages downloaded: {total}")
        
        # Cleanup old files
        client.cleanup_old_files(hours=48)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == '__main__':
    main()
