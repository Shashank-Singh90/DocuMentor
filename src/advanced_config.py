import json
import os
import time
import psutil
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from datetime import datetime, timedelta

@dataclass
class PerformanceConfig:
    """Dynamic performance configuration based on system resources"""
    
    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    quality_threshold: float = 50.0
    
    # Retrieval settings
    default_k: int = 5
    max_k: int = 10
    mmr_lambda: float = 0.7
    similarity_threshold: float = 0.7
    
    # ChromaDB settings
    batch_size: int = 100
    connection_timeout: int = 30
    max_retries: int = 3
    
    # LLM settings
    temperature: float = 0.1
    max_tokens: int = 512
    context_window: int = 4096
    cache_size: int = 200
    cache_ttl: int = 3600
    
    # System settings
    num_threads: int = 4
    memory_limit_gb: float = 8.0
    enable_gpu: bool = False

class ConfigManager:
    """Advanced configuration manager with auto-tuning"""
    
    def __init__(self, config_path: str = "./config/performance_config.yaml"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.performance_history = []
        self.auto_tune_enabled = True
        self.tune_lock = threading.Lock()
        
        # FIXED: Get system stats first, before loading config
        self.system_stats = self._get_system_stats()
        
        # Load or create config (now system_stats is available)
        self.config = self._load_or_create_config()
        
    def _get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            
            # Check for GPU (simplified detection)
            gpu_available = False
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                gpu_available = len(gpus) > 0
            except ImportError:
                # Fallback GPU detection for Windows
                try:
                    import subprocess
                    result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
                    gpu_available = result.returncode == 0
                except (FileNotFoundError, subprocess.SubprocessError):
                    gpu_available = False
            
            # Disk usage - handle Windows/Unix differences
            try:
                if os.name == 'nt':  # Windows
                    disk_usage = psutil.disk_usage('C:\\').percent
                else:  # Unix/Linux
                    disk_usage = psutil.disk_usage('/').percent
            except:
                disk_usage = 50.0  # Default fallback
            
            return {
                'total_memory_gb': memory.total / (1024**3),
                'available_memory_gb': memory.available / (1024**3),
                'cpu_cores': cpu_count,
                'cpu_threads': psutil.cpu_count(logical=True),
                'gpu_available': gpu_available,
                'disk_usage': disk_usage
            }
        except Exception as e:
            print(f"Warning: Could not gather system stats: {e}")
            # Return safe defaults
            return {
                'total_memory_gb': 8.0,
                'available_memory_gb': 4.0,
                'cpu_cores': 4,
                'cpu_threads': 4,
                'gpu_available': False,
                'disk_usage': 50.0
            }
    
    def _calculate_optimal_config(self) -> PerformanceConfig:
        """Calculate optimal configuration based on system resources"""
        stats = self.system_stats  # Now this exists!
        
        # Memory-based optimizations
        if stats['total_memory_gb'] >= 16:
            # High-end system
            config = PerformanceConfig(
                chunk_size=1200,
                chunk_overlap=240,
                batch_size=200,
                default_k=8,
                max_k=15,
                context_window=4096,
                cache_size=500,
                num_threads=min(stats['cpu_threads'], 8),
                memory_limit_gb=stats['total_memory_gb'] * 0.7,
                enable_gpu=stats['gpu_available']
            )
        elif stats['total_memory_gb'] >= 8:
            # Mid-range system
            config = PerformanceConfig(
                chunk_size=1000,
                chunk_overlap=200,
                batch_size=150,
                default_k=5,
                max_k=10,
                context_window=2048,
                cache_size=200,
                num_threads=min(stats['cpu_threads'], 6),
                memory_limit_gb=stats['total_memory_gb'] * 0.6,
                enable_gpu=stats['gpu_available']
            )
        else:
            # Resource-constrained system
            config = PerformanceConfig(
                chunk_size=800,
                chunk_overlap=160,
                batch_size=50,
                default_k=3,
                max_k=6,
                context_window=1024,
                cache_size=100,
                num_threads=min(stats['cpu_threads'], 4),
                memory_limit_gb=stats['total_memory_gb'] * 0.5,
                enable_gpu=False  # Disable GPU to conserve memory
            )
        
        print(f"Calculated optimal config for {stats['total_memory_gb']:.1f}GB RAM system")
        return config
    
    def _load_or_create_config(self) -> PerformanceConfig:
        """Load existing config or create optimal one"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_dict = yaml.safe_load(f)
                    config = PerformanceConfig(**config_dict)
                    print(f"Loaded configuration from {self.config_path}")
                    return config
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
        
        # Create optimal config
        config = self._calculate_optimal_config()
        self.save_config(config)
        return config
    
    def save_config(self, config: Optional[PerformanceConfig] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(asdict(config), f, default_flow_style=False, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def apply_preset(self, preset_name: str):
        """Apply performance preset configurations"""
        presets = {
            'speed': PerformanceConfig(
                chunk_size=800,
                chunk_overlap=100,
                default_k=3,
                max_k=5,
                temperature=0.0,
                max_tokens=256,
                context_window=2048,
                cache_size=500,
                batch_size=200
            ),
            'quality': PerformanceConfig(
                chunk_size=1500,
                chunk_overlap=300,
                default_k=8,
                max_k=15,
                temperature=0.3,
                max_tokens=1024,
                context_window=4096,
                cache_size=100,
                batch_size=50
            ),
            'balanced': PerformanceConfig(
                chunk_size=1000,
                chunk_overlap=200,
                default_k=5,
                max_k=10,
                temperature=0.1,
                max_tokens=512,
                context_window=4096,
                cache_size=200,
                batch_size=100
            ),
            'memory_saver': PerformanceConfig(
                chunk_size=600,
                chunk_overlap=100,
                default_k=3,
                max_k=5,
                temperature=0.0,
                max_tokens=256,
                context_window=1024,
                cache_size=50,
                batch_size=25
            )
        }
        
        if preset_name in presets:
            self.config = presets[preset_name]
            self.save_config()
            print(f"Applied '{preset_name}' preset configuration")
        else:
            available = ', '.join(presets.keys())
            print(f"Unknown preset '{preset_name}'. Available: {available}")
    
    def record_performance(self, operation: str, response_time: float, 
                         success: bool, **kwargs):
        """Record performance metrics for auto-tuning"""
        record = {
            'timestamp': time.time(),
            'operation': operation,
            'response_time': response_time,
            'success': success,
            'system_memory_usage': psutil.virtual_memory().percent,
            'system_cpu_usage': psutil.cpu_percent(interval=None),
            **kwargs
        }
        
        self.performance_history.append(record)
        
        # Keep only last 1000 records
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        # Auto-tune if enabled and we have enough data
        if (self.auto_tune_enabled and 
            len(self.performance_history) > 50 and 
            len(self.performance_history) % 25 == 0):
            self._auto_tune()
    
    def _auto_tune(self):
        """Automatically tune configuration based on performance history"""
        with self.tune_lock:
            try:
                recent_records = self.performance_history[-50:]
                
                # Calculate performance metrics
                avg_response_time = sum(r['response_time'] for r in recent_records) / len(recent_records)
                success_rate = sum(1 for r in recent_records if r['success']) / len(recent_records)
                avg_memory_usage = sum(r['system_memory_usage'] for r in recent_records) / len(recent_records)
                
                print(f"Auto-tune analysis: {avg_response_time:.2f}s avg, {success_rate:.2%} success, {avg_memory_usage:.1f}% memory")
                
                # Tuning logic
                config_changed = False
                
                # If response time is too slow and memory usage is low, increase batch size
                if avg_response_time > 15 and avg_memory_usage < 70:
                    old_batch = self.config.batch_size
                    self.config.batch_size = min(self.config.batch_size + 25, 300)
                    if self.config.batch_size != old_batch:
                        print(f"Auto-tune: Increased batch size {old_batch} -> {self.config.batch_size}")
                        config_changed = True
                
                # If memory usage is too high, reduce batch size and cache
                elif avg_memory_usage > 85:
                    old_batch = self.config.batch_size
                    old_cache = self.config.cache_size
                    self.config.batch_size = max(self.config.batch_size - 25, 25)
                    self.config.cache_size = max(self.config.cache_size - 50, 50)
                    
                    if self.config.batch_size != old_batch or self.config.cache_size != old_cache:
                        print(f"Auto-tune: Reduced batch {old_batch}->{self.config.batch_size}, cache {old_cache}->{self.config.cache_size}")
                        config_changed = True
                
                # If success rate is low, be more conservative
                elif success_rate < 0.9:
                    old_retries = self.config.max_retries
                    old_timeout = self.config.connection_timeout
                    self.config.max_retries = min(self.config.max_retries + 1, 5)
                    self.config.connection_timeout = min(self.config.connection_timeout + 10, 60)
                    
                    if (self.config.max_retries != old_retries or 
                        self.config.connection_timeout != old_timeout):
                        print(f"Auto-tune: Increased reliability - retries {old_retries}->{self.config.max_retries}, timeout {old_timeout}->{self.config.connection_timeout}")
                        config_changed = True
                
                if config_changed:
                    self.save_config()
                    
            except Exception as e:
                print(f"Auto-tune failed: {e}")
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate performance report for the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        recent_records = [r for r in self.performance_history if r['timestamp'] > cutoff_time]
        
        if not recent_records:
            return {"error": "No performance data available"}
        
        # Calculate statistics
        response_times = [r['response_time'] for r in recent_records]
        success_count = sum(1 for r in recent_records if r['success'])
        
        return {
            'period_hours': hours,
            'total_operations': len(recent_records),
            'overall_success_rate': success_count / len(recent_records),
            'avg_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'current_config': asdict(self.config),
            'system_stats': self.system_stats
        }
    
    def export_config_template(self, template_path: str = "./config_template.yaml"):
        """Export a configuration template with comments"""
        template_content = f"""# Docu RAG Performance Configuration Template
# Automatically generated based on your system specifications

# Document Processing Settings
chunk_size: {self.config.chunk_size}          # Size of text chunks (characters)
chunk_overlap: {self.config.chunk_overlap}        # Overlap between chunks (characters)
quality_threshold: {self.config.quality_threshold}   # Minimum chunk quality score

# Retrieval Settings  
default_k: {self.config.default_k}              # Default number of documents to retrieve
max_k: {self.config.max_k}                 # Maximum number of documents to retrieve
mmr_lambda: {self.config.mmr_lambda}           # MMR diversity parameter (0=diverse, 1=similar)
similarity_threshold: {self.config.similarity_threshold}  # Minimum similarity score threshold

# ChromaDB Settings
batch_size: {self.config.batch_size}           # Batch size for vector operations
connection_timeout: {self.config.connection_timeout}    # Connection timeout (seconds)
max_retries: {self.config.max_retries}           # Maximum retry attempts

# LLM Settings
temperature: {self.config.temperature}         # LLM creativity (0=deterministic, 1=creative)
max_tokens: {self.config.max_tokens}          # Maximum response length
context_window: {self.config.context_window}     # Maximum context size
cache_size: {self.config.cache_size}          # Response cache size
cache_ttl: {self.config.cache_ttl}         # Cache time-to-live (seconds)

# System Settings
num_threads: {self.config.num_threads}           # Number of processing threads
memory_limit_gb: {self.config.memory_limit_gb}     # Memory usage limit
enable_gpu: {self.config.enable_gpu}        # Enable GPU acceleration
"""
        
        try:
            with open(template_path, 'w') as f:
                f.write(template_content)
            print(f"Configuration template exported to {template_path}")
        except Exception as e:
            print(f"Failed to export template: {e}")

# Simple test function
def test_config():
    """Simple test to verify the ConfigManager works"""
    try:
        print("Testing ConfigManager...")
        config_manager = ConfigManager()
        print("✓ ConfigManager initialized successfully")
        
        config_manager.apply_preset('balanced')
        print("✓ Applied balanced preset")
        
        # Test system stats
        print(f"✓ System stats: {config_manager.system_stats}")
        
        print("✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_config()
