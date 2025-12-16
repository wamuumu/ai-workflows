from pydantic import BaseModel, Field

class MetricSet(BaseModel):
    time_taken: float = 0
    number_of_calls: int = 0

class MetricSchema(BaseModel):
    generation: MetricSet = Field(default_factory=MetricSet)
    chat: MetricSet = Field(default_factory=MetricSet)
    execution: MetricSet = Field(default_factory=MetricSet)

class MetricUtils:
    
    _metrics: MetricSchema = MetricSchema() 

    @classmethod
    def update_generation_metrics(cls, kwargs) -> None:
        cls._metrics.generation.time_taken += kwargs.get("time_taken", 0)
        cls._metrics.generation.number_of_calls += 1

    @classmethod
    def update_chat_metrics(cls, kwargs) -> None:
        cls._metrics.chat.time_taken += kwargs.get("time_taken", 0)
        cls._metrics.chat.number_of_calls += 1
    
    @classmethod
    def update_execution_metrics(cls, kwargs) -> None:
        cls._metrics.execution.time_taken += kwargs.get("time_taken", 0)
        cls._metrics.execution.number_of_calls += 1
    
    @classmethod
    def display_metrics(cls) -> None:
        print("\nOrchestrator Metrics:")
        dumped_metrics = cls._metrics.model_dump()
        for phase, metrics in dumped_metrics.items():
            print(f"  {phase.capitalize()}:")
            for metric_name, value in metrics.items():
                if metric_name == "time_taken":
                    print(f"    {metric_name.replace('_', ' ').capitalize()}: {value:.2f} seconds")
                else:
                    print(f"    {metric_name.replace('_', ' ').capitalize()}: {value}")