from django.db import models

# Models of Prediction Data.
class PredictionData(models.Model):
    x = models.FloatField()
    y = models.FloatField()
    SAMPLE_1 = models.FloatField()
    SAMPLE_2 = models.FloatField()
    predicted_probabilities = models.FloatField()

    def __str__(self):
        return f"Sample {self.id}: x={self.x}, y={self.y}, SAMPLE_1={self.SAMPLE_1}, SAMPLE_2={self.SAMPLE_2}, predicted_probabilities={self.predicted_probabilities}"