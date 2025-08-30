from django.core.management.base import BaseCommand
from django.core.management import call_command
from app.models import Institute

class Command(BaseCommand):
    help = 'Load institute demographic data from fixtures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing institute data before loading',
        )
        parser.add_argument(
            '--fixture',
            type=str,
            default='institutes',
            help='Name of the fixture file to load (default: institutes)',
        )

    def handle(self, *args, **options):
        self.stdout.write("Loading institute demographic data from fixtures...")
        
        if options['clear']:
            self.stdout.write("Clearing existing institute data...")
            Institute.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Deleted all existing institutes")
            )
        
        # Load the fixture data
        try:
            self.stdout.write(f"Loading fixture: {options['fixture']}.json")
            call_command('loaddata', options['fixture'])
            
            # Get summary statistics
            total_institutes = Institute.objects.count()
            approved_institutes = Institute.objects.filter(registration_status='approved').count()
            
            # District breakdown
            district_counts = {}
            for institute in Institute.objects.all():
                district = institute.district or 'Unknown'
                if district not in district_counts:
                    district_counts[district] = {'total': 0, 'male_students': 0, 'female_students': 0}
                district_counts[district]['total'] += 1
                district_counts[district]['male_students'] += institute.male_students_count
                district_counts[district]['female_students'] += institute.female_students_count
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n📊 Successfully loaded institute data!\n"
                    f"   Total institutes: {total_institutes}\n"
                    f"   Approved institutes: {approved_institutes}\n"
                    f"   Districts covered: {len(district_counts)}"
                )
            )
            
            # Show top 10 districts by institute count
            self.stdout.write(self.style.SUCCESS("\n🏛️ Top Districts by Institute Count:"))
            sorted_districts = sorted(district_counts.items(), key=lambda x: x[1]['total'], reverse=True)
            for district, stats in sorted_districts[:10]:
                total_students = stats['male_students'] + stats['female_students']
                male_pct = (stats['male_students'] / total_students * 100) if total_students > 0 else 0
                female_pct = (stats['female_students'] / total_students * 100) if total_students > 0 else 0
                
                self.stdout.write(
                    f"   {district:20} | {stats['total']:3d} institutes | "
                    f"{total_students:5d} students | M: {male_pct:4.1f}% F: {female_pct:4.1f}%"
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error loading fixture: {e}")
            )
