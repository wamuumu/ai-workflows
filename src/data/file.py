from data.base import BaseData

class CsvFiles(BaseData):
    """Mocked CSV files data source."""

    def __init__(self):
        super().__init__(name="csv_files", description="Mocked CSV files data source.")

    @property
    def data(self) -> dict:
        return {
            "sales_data": [
                {"date": "2024-01-01", "product": "Laptop", "quantity": 5, "price": 1200.00, "region": "North"},
                {"date": "2024-01-02", "product": "Mouse", "quantity": 15, "price": 25.50, "region": "South"},
                {"date": "2024-01-03", "product": "Keyboard", "quantity": 8, "price": 75.00, "region": "North"},
                {"date": "2024-01-04", "product": "Laptop", "quantity": 3, "price": 1200.00, "region": "East"},
                {"date": "2024-01-05", "product": "Monitor", "quantity": 10, "price": 350.00, "region": "West"},
            ],
            "employee_data": [
                {"id": 1, "name": "Alice Smith", "department": "Engineering", "salary": 85000, "years": 3},
                {"id": 2, "name": "Bob Johnson", "department": "Sales", "salary": 65000, "years": 5},
                {"id": 3, "name": "Carol White", "department": "Engineering", "salary": 95000, "years": 7},
                {"id": 4, "name": "David Brown", "department": "Marketing", "salary": 70000, "years": 2},
                {"id": 5, "name": "Eve Davis", "department": "Engineering", "salary": 90000, "years": 4},
            ],
            "weather_data": [
                {"city": "Milan", "date": "2024-12-01", "temp": 8, "humidity": 75, "condition": "cloudy"},
                {"city": "Milan", "date": "2024-12-02", "temp": 10, "humidity": 70, "condition": "sunny"},
                {"city": "Rome", "date": "2024-12-01", "temp": 15, "humidity": 60, "condition": "sunny"},
                {"city": "Rome", "date": "2024-12-02", "temp": 14, "humidity": 65, "condition": "rainy"},
            ]
        }