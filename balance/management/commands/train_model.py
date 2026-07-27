from django.core.management.base import BaseCommand

from balance.services.ai_service import train_model


class Command(BaseCommand):
    help = "Training the global prediction model"

    def handle(self, *args, **kwargs):
        
        self.stdout.write("Training model...")
        
        train_model()
        
        self.stdout.write(self.style.SUCCESS("Correctly trained model"))