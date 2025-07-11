from django.db import models
from django.forms.models import model_to_dict


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # this is for development prepuces. it gives the ability to call to_dict on a query object to print the results in json format
    @property
    def to_dict(self):
        return model_to_dict(self)

    class Meta:
        abstract = True
