from .forms import StudyActivityForm, LiveStudyActivityForm, SportActivityForm, LiveSportActivityForm, SubjectForm

def activity_forms(request):
    study_form = StudyActivityForm()
    sport_form = SportActivityForm()
    live_study_form = LiveStudyActivityForm()
    live_sport_form = LiveSportActivityForm()
    subject_form = SubjectForm()
    
    live_study_start_datetime = None
    live_study_end_datetime = None
    live_study_paused_duration = 0
    
    live_sport_start_datetime = None
    live_sport_end_datetime = None
    live_sport_paused_duration = 0

    # Comprobación si es un formulario con errores
    study_form_data = request.session.pop("study_form_data", None)
    open_study_modal = request.session.pop("open_study_modal", False)
    
    live_study_form_data = request.session.pop("live_study_form_data", None)
    open_live_study = request.session.pop("open_live_study", False)
    live_study_finished = request.session.pop("live_study_finished", False)
    
    sport_form_data = request.session.pop("sport_form_data", None)
    open_sport_modal = request.session.pop("open_sport_modal", False)
    
    live_sport_form_data = request.session.pop("live_sport_form_data", None)
    open_live_sport = request.session.pop("open_live_sport", False)
    live_sport_finished = request.session.pop("live_sport_finished", False)

    if study_form_data:
        study_form = StudyActivityForm(study_form_data)
        
    if live_study_form_data:
        live_study_form = LiveStudyActivityForm(live_study_form_data)
        
        live_study_start_datetime = live_study_form_data.get("start_datetime")
        live_study_end_datetime = live_study_form_data.get("end_datetime")
        live_study_paused_duration = live_study_form_data.get("paused_duration", 0)
        
    if sport_form_data:
        sport_form = SportActivityForm(sport_form_data)
        
    if live_sport_form_data:
        live_sport_form = LiveSportActivityForm(live_sport_form_data)
        
        live_sport_start_datetime = live_sport_form_data.get("start_datetime")
        live_sport_end_datetime = live_sport_form_data.get("end_datetime")
        live_sport_paused_duration = live_sport_form_data.get("paused_duration", 0)
        
    return {
        "study_form": study_form,
        "live_study_form": live_study_form,
        "live_study_finished": live_study_finished,
        "live_study_start_datetime": live_study_start_datetime,
        "live_study_end_datetime": live_study_end_datetime,
        "live_study_paused_duration": live_study_paused_duration,
        
        "sport_form": sport_form,
        "live_sport_form": live_sport_form,
        "live_sport_finished": live_sport_finished,
        "live_sport_start_datetime": live_sport_start_datetime,
        "live_sport_end_datetime": live_sport_end_datetime,
        "live_sport_paused_duration": live_sport_paused_duration,
        
        "subject_form": subject_form,
        
        "open_study_modal": open_study_modal,
        "open_live_study": open_live_study,
        
        "open_sport_modal": open_sport_modal,
        "open_live_sport": open_live_sport,
    }