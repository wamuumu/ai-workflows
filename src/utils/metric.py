from pydantic import BaseModel, Field

class MetricSet(BaseModel):
    time_taken: float = 0
    number_of_calls: int = 0 
    total_tokens: int = 0 # input + output tokens

class MetricSchema(BaseModel):
    generation: MetricSet = Field(default_factory=MetricSet)
    chat: MetricSet = Field(default_factory=MetricSet)
    execution: MetricSet = Field(default_factory=MetricSet)

class MetricUtils:
    
    _metrics: MetricSchema = MetricSchema() 

    @classmethod
    def update(cls, category: str, start_time: float, end_time: float, tokens: int) -> None:

        fields = MetricSchema.model_fields

        if category not in fields:
            raise ValueError(f"Invalid metric type: {category}. Valid types are: {list(fields.keys())}")
        
        metric_set: MetricSet = getattr(cls._metrics, category)
        metric_set.time_taken += end_time - start_time
        metric_set.number_of_calls += 1
        metric_set.total_tokens += tokens
    
    @classmethod
    def display(cls) -> None:
        print("\nOrchestrator Metrics:")
        dumped_metrics = cls._metrics.model_dump()
        for phase, metrics in dumped_metrics.items():
            print(f"  {phase.capitalize()}:")
            for metric_name, value in metrics.items():
                if metric_name == "time_taken":
                    print(f"    {metric_name.replace('_', ' ').capitalize()}: {value:.2f} seconds")
                else:
                    print(f"    {metric_name.replace('_', ' ').capitalize()}: {value}")