from django import forms
from performance.models import Evaluation, EvaluationCategory

class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['category', 'score', 'evaluation_date', 'content', 'evidence_reference']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'Điểm 0-100'}),
            'evaluation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Nội dung đánh giá...'}),
            'evidence_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }
