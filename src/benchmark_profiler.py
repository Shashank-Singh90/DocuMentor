import time
import psutil
import threading
import statistics
import json
import os
import gc
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import cProfile
import pstats
from io import StringIO
import tracemalloc
from contextlib import contextmanager
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

@dataclass
class BenchmarkResult:
    """Comprehensive benchmark result"""
    operation: str
    duration: float
    memory_before: float
    memory_after: float
    memory_peak: float
    cpu_percent: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SystemProfiler:
    """Advanced system profiling and benchmarking"""
    
    def __init__(self, output_dir: str = "./benchmarks"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.results: List[BenchmarkResult] = []
        self.profiling_enabled = False
        self.memory_monitoring = False
        
        # Performance thresholds
        self.thresholds = {
            'document_processing': {'time': 30.0, 'memory': 1024},  # MB
            'retrieval': {'time': 5.0, 'memory': 512},
            'llm_response': {'time': 20.0, 'memory': 512},
            'vector_search': {'time': 2.0, 'memory': 256}
        }
    
    def start_memory_monitoring(self):
        """Start continuous memory monitoring"""
        if not self.memory_monitoring:
            tracemalloc.start()
            self.memory_monitoring = True
    
    def stop_memory_monitoring(self):
        """Stop memory monitoring and get snapshot"""
        if self.memory_monitoring:
            snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
            self.memory_monitoring = False
            return snapshot
        return None
    
    @contextmanager
    def profile_operation(self, operation_name: str, 
                         enable_profiling: bool = False,
                         enable_memory_tracking: bool = True):
        """Context manager for profiling operations"""
        
        # Start monitoring
        if enable_memory_tracking:
            self.start_memory_monitoring()
        
        profiler = None
        if enable_profiling:
            profiler = cProfile.Profile()
            profiler.enable()
        
        # Get initial metrics
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.time()
        start_cpu_times = process.cpu_times()
        
        success = True
        error = None
        metadata = {}
        
        try:
            yield metadata  # Allow caller to add metadata
            
        except Exception as e:
            success = False
            error = str(e)
            raise
            
        finally:
            # Calculate metrics
            duration = time.time() - start_time
            end_cpu_times = process.cpu_times()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            
            # CPU usage calculation
            cpu_time_used = (end_cpu_times.user - start_cpu_times.user + 
                           end_cpu_times.system - start_cpu_times.system)
            cpu_percent = (cpu_time_used / duration) * 100 if duration > 0 else 0
            
            # Memory peak detection
            memory_peak = memory_after  # Simplified - could track peak during operation
            
            # Stop profiling
            if profiler:
                profiler.disable()
                self._save_profile_stats(operation_name, profiler)
            
            # Memory snapshot
            memory_snapshot = None
            if enable_memory_tracking:
                memory_snapshot = self.stop_memory_monitoring()
                if memory_snapshot:
                    self._analyze_memory_usage(operation_name, memory_snapshot)
            
            # Create result
            result = BenchmarkResult(
                operation=operation_name,
                duration=duration,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=memory_peak,
                cpu_percent=cpu_percent,
                success=success,
                error=error,
                metadata=metadata
            )
            
            self.results.append(result)
            
            # Check against thresholds
            self._check_thresholds(result)
    
    def _save_profile_stats(self, operation_name: str, profiler: cProfile.Profile):
        """Save profiling statistics to file"""
        try:
            stats_output = StringIO()
            stats = pstats.Stats(profiler, stream=stats_output)
            stats.sort_stats('cumulative')
            stats.print_stats(20)  # Top 20 functions
            
            profile_file = self.output_dir / f"profile_{operation_name}_{int(time.time())}.txt"
            with open(profile_file, 'w') as f:
                f.write(stats_output.getvalue())
            
            print(f"📊 Profile saved to {profile_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to save profile: {e}")
    
    def _analyze_memory_usage(self, operation_name: str, snapshot):
        """Analyze memory usage from tracemalloc snapshot"""
        try:
            top_stats = snapshot.statistics('lineno')
            
            analysis_file = self.output_dir / f"memory_{operation_name}_{int(time.time())}.txt"
            with open(analysis_file, 'w') as f:
                f.write(f"Memory Analysis for {operation_name}\n")
                f.write("=" * 50 + "\n")
                
                total_size = sum(stat.size for stat in top_stats)
                f.write(f"Total memory usage: {total_size / 1024 / 1024:.2f} MB\n\n")
                
                f.write("Top 10 memory consumers:\n")
                for stat in top_stats[:10]:
                    f.write(f"{stat.traceback.format()[-1]}: {stat.size / 1024:.1f} KB\n")
            
            print(f"🧠 Memory analysis saved to {analysis_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to analyze memory: {e}")
    
    def _check_thresholds(self, result: BenchmarkResult):
        """Check if result exceeds performance thresholds"""
        operation_type = self._get_operation_type(result.operation)
        
        if operation_type in self.thresholds:
            threshold = self.thresholds[operation_type]
            
            warnings = []
            if result.duration > threshold['time']:
                warnings.append(f"Time: {result.duration:.2f}s > {threshold['time']}s")
            
            memory_used = result.memory_after - result.memory_before
            if memory_used > threshold['memory']:
                warnings.append(f"Memory: {memory_used:.1f}MB > {threshold['memory']}MB")
            
            if warnings:
                print(f"⚠️ Performance threshold exceeded for {result.operation}:")
                for warning in warnings:
                    print(f"   • {warning}")
    
    def _get_operation_type(self, operation_name: str) -> str:
        """Classify operation type for threshold checking"""
        operation_lower = operation_name.lower()
        
        if any(keyword in operation_lower for keyword in ['document', 'process', 'chunk']):
            return 'document_processing'
        elif any(keyword in operation_lower for keyword in ['retriev', 'search', 'vector']):
            return 'retrieval'
        elif any(keyword in operation_lower for keyword in ['llm', 'generate', 'chat']):
            return 'llm_response'
        else:
            return 'other'
    
    def benchmark_complete_pipeline(self, rag_system, test_questions: List[str]):
        """Benchmark complete RAG pipeline with test questions"""
        print("🚀 Running complete pipeline benchmark...")
        
        pipeline_results = []
        
        for i, question in enumerate(test_questions, 1):
            print(f"📝 Test {i}/{len(test_questions)}: {question[:50]}...")
            
            with self.profile_operation(f"pipeline_question_{i}", 
                                      enable_profiling=True) as metadata:
                metadata['question'] = question
                metadata['question_length'] = len(question)
                
                # Time individual components
                component_times = {}
                
                # Document retrieval
                retrieval_start = time.time()
                try:
                    if hasattr(rag_system, 'retriever') and rag_system.retriever:
                        docs = rag_system.retriever.retrieve_documents(question)
                        component_times['retrieval'] = time.time() - retrieval_start
                        metadata['docs_retrieved'] = len(docs)
                    else:
                        docs = []
                        component_times['retrieval'] = 0
                        metadata['docs_retrieved'] = 0
                except Exception as e:
                    component_times['retrieval'] = time.time() - retrieval_start
                    metadata['retrieval_error'] = str(e)
                    docs = []
                
                # LLM generation
                llm_start = time.time()
                try:
                    if hasattr(rag_system, 'ask_question_optimized'):
                        result = rag_system.ask_question_optimized(question)
                        answer = result.get('answer', 'No answer')
                        component_times['llm'] = time.time() - llm_start
                        metadata['answer_length'] = len(answer)
                        metadata['confidence'] = result.get('confidence', 0)
                    else:
                        answer = "System not initialized"
                        component_times['llm'] = time.time() - llm_start
                        metadata['answer_length'] = len(answer)
                except Exception as e:
                    component_times['llm'] = time.time() - llm_start
                    metadata['llm_error'] = str(e)
                    answer = f"Error: {str(e)}"
                
                metadata['component_times'] = component_times
                
                pipeline_results.append({
                    'question': question,
                    'answer': answer,
                    'total_time': component_times.get('retrieval', 0) + component_times.get('llm', 0),
                    'retrieval_time': component_times.get('retrieval', 0),
                    'llm_time': component_times.get('llm', 0),
                    'docs_count': metadata.get('docs_retrieved', 0)
                })
        
        # Save detailed results
        self._save_pipeline_results(pipeline_results)
        return pipeline_results
    
    def _save_pipeline_results(self, results: List[Dict]):
        """Save pipeline benchmark results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.output_dir / f"pipeline_benchmark_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Pipeline results saved to {results_file}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    
    def benchmark_component_scalability(self, component_func: Callable, 
                                      test_sizes: List[int], 
                                      component_name: str):
        """Benchmark component performance across different input sizes"""
        print(f"📈 Benchmarking {component_name} scalability...")
        
        scalability_results = []
        
        for size in test_sizes:
            print(f"   Testing with size: {size}")
            
            # Generate test data based on size
            if 'retrieval' in component_name.lower():
                test_data = "test query " * max(1, size // 10)
            elif 'document' in component_name.lower():
                test_data = ["test document content " * size for _ in range(size)]
            else:
                test_data = "test input " * size
            
            with self.profile_operation(f"{component_name}_size_{size}") as metadata:
                metadata['input_size'] = size
                
                try:
                    result = component_func(test_data)
                    metadata['output_size'] = len(result) if hasattr(result, '__len__') else 1
                except Exception as e:
                    metadata['error'] = str(e)
                    result = None
            
            # Get the latest result
            latest_result = self.results[-1]
            scalability_results.append({
                'size': size,
                'duration': latest_result.duration,
                'memory_used': latest_result.memory_after - latest_result.memory_before,
                'success': latest_result.success
            })
        
        # Create scalability plot
        self._create_scalability_plot(component_name, scalability_results)
        return scalability_results
    
    def _create_scalability_plot(self, component_name: str, results: List[Dict]):
        """Create scalability visualization"""
        try:
            sizes = [r['size'] for r in results if r['success']]
            durations = [r['duration'] for r in results if r['success']]
            memory_usage = [r['memory_used'] for r in results if r['success']]
            
            if not sizes:
                print("⚠️ No successful results to plot")
                return
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Duration plot
            ax1.plot(sizes, durations, 'b-o', linewidth=2, markersize=6)
            ax1.set_xlabel('Input Size')
            ax1.set_ylabel('Duration (seconds)')
            ax1.set_title(f'{component_name} - Processing Time')
            ax1.grid(True, alpha=0.3)
            
            # Memory plot
            ax2.plot(sizes, memory_usage, 'r-s', linewidth=2, markersize=6)
            ax2.set_xlabel('Input Size')
            ax2.set_ylabel('Memory Usage (MB)')
            ax2.set_title(f'{component_name} - Memory Usage')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_file = self.output_dir / f"scalability_{component_name}_{timestamp}.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"📊 Scalability plot saved to {plot_file}")
            
        except Exception as e:
            print(f"❌ Failed to create scalability plot: {e}")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.results:
            return {"error": "No benchmark results available"}
        
        # Overall statistics
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        durations = [r.duration for r in successful_results]
        memory_usage = [r.memory_after - r.memory_before for r in successful_results]
        cpu_usage = [r.cpu_percent for r in successful_results]
        
        # Group by operation type
        by_operation = {}
        for result in successful_results:
            op_type = self._get_operation_type(result.operation)
            if op_type not in by_operation:
                by_operation[op_type] = []
            by_operation[op_type].append(result)
        
        operation_stats = {}
        for op_type, results in by_operation.items():
            op_durations = [r.duration for r in results]
            op_memory = [r.memory_after - r.memory_before for r in results]
            
            operation_stats[op_type] = {
                'count': len(results),
                'avg_duration': statistics.mean(op_durations),
                'median_duration': statistics.median(op_durations),
                'std_duration': statistics.stdev(op_durations) if len(op_durations) > 1 else 0,
                'avg_memory': statistics.mean(op_memory),
                'max_memory': max(op_memory),
                'success_rate': len(results) / len([r for r in self.results if self._get_operation_type(r.operation) == op_type])
            }
        
        # Performance recommendations
        recommendations = self._generate_recommendations(operation_stats)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_operations': len(self.results),
            'successful_operations': len(successful_results),
            'failed_operations': len(failed_results),
            'overall_success_rate': len(successful_results) / len(self.results) if self.results else 0,
            
            'performance_summary': {
                'avg_duration': statistics.mean(durations) if durations else 0,
                'median_duration': statistics.median(durations) if durations else 0,
                'p95_duration': sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
                'avg_memory_usage': statistics.mean(memory_usage) if memory_usage else 0,
                'max_memory_usage': max(memory_usage) if memory_usage else 0,
                'avg_cpu_usage': statistics.mean(cpu_usage) if cpu_usage else 0
            },
            
            'by_operation_type': operation_stats,
            'recommendations': recommendations,
            
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'total_memory': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
                'available_memory': psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
                'disk_usage': psutil.disk_usage('.').percent if os.path.exists('.') else 0
            }
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"performance_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📋 Performance report saved to {report_file}")
        except Exception as e:
            print(f"❌ Failed to save report: {e}")
        
        return report
    
    def _generate_recommendations(self, operation_stats: Dict) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        for op_type, stats in operation_stats.items():
            # Duration recommendations
            if stats['avg_duration'] > self.thresholds.get(op_type, {}).get('time', float('inf')):
                if op_type == 'document_processing':
                    recommendations.append(f"📄 {op_type}: Consider reducing chunk size or batch size to improve processing speed")
                elif op_type == 'retrieval':
                    recommendations.append(f"🔍 {op_type}: Consider reducing k value or implementing better caching")
                elif op_type == 'llm_response':
                    recommendations.append(f"🤖 {op_type}: Consider reducing context window or max tokens")
            
            # Memory recommendations
            if stats['avg_memory'] > self.thresholds.get(op_type, {}).get('memory', float('inf')):
                recommendations.append(f"💾 {op_type}: High memory usage detected - consider smaller batch sizes")
            
            # Reliability recommendations
            if stats['success_rate'] < 0.95:
                recommendations.append(f"⚠️ {op_type}: Low success rate ({stats['success_rate']:.1%}) - increase timeout or retries")
        
        # General system recommendations
        system_memory = psutil.virtual_memory()
        if system_memory.percent > 85:
            recommendations.append("🖥️ System memory usage is high - consider closing other applications")
        
        if not recommendations:
            recommendations.append("✅ System performance is within acceptable ranges")
        
        return recommendations
    
    def clear_results(self):
        """Clear all benchmark results"""
        self.results.clear()
        print("🧹 Benchmark results cleared")

# Specialized benchmark functions
class RAGBenchmarkSuite:
    """Specialized benchmark suite for RAG systems"""
    
    def __init__(self, profiler: SystemProfiler):
        self.profiler = profiler
    
    def benchmark_retrieval_accuracy(self, rag_system, test_cases: List[Dict]):
        """Benchmark retrieval accuracy with known correct answers"""
        print("🎯 Benchmarking retrieval accuracy...")
        
        accuracy_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            question = test_case['question']
            expected_keywords = test_case.get('expected_keywords', [])
            
            with self.profiler.profile_operation(f"accuracy_test_{i}") as metadata:
                metadata.update(test_case)
                
                try:
                    if hasattr(rag_system, 'retriever') and rag_system.retriever:
                        docs = rag_system.retriever.retrieve_documents(question)
                        
                        # Calculate relevance score
                        relevance_score = self._calculate_relevance_score(docs, expected_keywords)
                        metadata['relevance_score'] = relevance_score
                        
                        accuracy_results.append({
                            'question': question,
                            'docs_retrieved': len(docs),
                            'relevance_score': relevance_score,
                            'expected_keywords': expected_keywords
                        })
                    else:
                        metadata['error'] = "Retriever not available"
                        
                except Exception as e:
                    metadata['error'] = str(e)
        
        return accuracy_results
    
    def _calculate_relevance_score(self, docs: List, expected_keywords: List[str]) -> float:
        """Calculate relevance score based on keyword presence"""
        if not expected_keywords or not docs:
            return 0.0
        
        total_score = 0
        for doc in docs:
            content = getattr(doc, 'page_content', str(doc)).lower()
            keyword_hits = sum(1 for keyword in expected_keywords if keyword.lower() in content)
            doc_score = keyword_hits / len(expected_keywords)
            total_score += doc_score
        
        return total_score / len(docs)

# Usage example
if __name__ == "__main__":
    # Create profiler
    profiler = SystemProfiler()
    
    # Example usage
    test_questions = [
        "What is Python?",
        "How do I install packages?",
        "Explain machine learning basics",
        "Database optimization techniques",
        "What are the best practices for API design?"
    ]
    
    # Example of profiling an operation
    with profiler.profile_operation("example_operation", enable_profiling=True) as metadata:
        # Simulate some work
        time.sleep(0.1)
        metadata['work_completed'] = True
    
    # Generate report
    report = profiler.generate_performance_report()
    print("\n📊 Performance Report Generated:")
    print(f"Total operations: {report['total_operations']}")
    print(f"Success rate: {report['overall_success_rate']:.2%}")
    
    if report['recommendations']:
        print("\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
