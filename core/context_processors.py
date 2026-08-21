from .forms import StudyActivityForm, LiveStudyActivityForm, SportActivityForm, LiveSportActivityForm

def activity_forms(request):
    study_form = StudyActivityForm()
    sport_form = SportActivityForm()
    open_study_modal = False
    open_sport_modal = False

    # Comprobación si es un formulario con errores
    study_form_data = request.session.pop("study_form_data", None)
    open_study_modal = request.session.pop("open_study_modal", False)
    
    sport_form_data = request.session.pop("sport_form_data", None)
    open_sport_modal = request.session.pop("open_sport_modal", False)

    if study_form_data:
        study_form = StudyActivityForm(study_form_data)
        
    if sport_form_data:
        sport_form = SportActivityForm(sport_form_data)
        
    return {
        "study_form": study_form,
        "live_study_form": LiveStudyActivityForm(),
        "sport_form": sport_form,
        "live_sport_form": LiveSportActivityForm(),
        "open_study_modal": open_study_modal,
        "open_sport_modal": open_sport_modal,
    }