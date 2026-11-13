"""Exercise actual Streamlit pages and native controls without a browser."""
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src.utils import ROOT

@pytest.mark.parametrize('page',['app.py','pages/1_Overview.py','pages/2_Login_Analysis.py',
                                'pages/3_Anomaly_Detection.py','pages/4_Live_Simulation.py','pages/5_Model_Performance.py'])
def test_pages(page):
    app=AppTest.from_file(str(ROOT/page),default_timeout=90).run()
    assert not app.exception, [e.message for e in app.exception]
    assert app.title or app.subheader

def test_filter_empty_and_search():
    app=AppTest.from_file(str(ROOT/'pages/2_Login_Analysis.py'),default_timeout=90).run()
    app.text_input[0].set_value('NO_SUCH_EVENT').run()
    assert not app.exception and app.info

def test_manual_form():
    app=AppTest.from_file(str(ROOT/'pages/3_Anomaly_Detection.py'),default_timeout=90).run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.dataframe)>=2
    app.text_input[1].set_value('invalid')
    app.button[0].click().run()
    assert app.error and not app.exception

def test_simulation_buttons():
    app=AppTest.from_file(str(ROOT/'pages/4_Live_Simulation.py'),default_timeout=90).run()
    for index in [0,1,2]:
        app.button[index].click().run()
        assert not app.exception
    assert len(app.session_state['sim_results'])==3
    app.button[3].click().run()
    assert not app.exception and not app.session_state['sim_results']

def test_overview_filter_consistency():
    app=AppTest.from_file(str(ROOT/'pages/1_Overview.py'),default_timeout=90).run()
    app.selectbox[0].select('Suspect').run()
    assert not app.exception
    assert app.metric[1].value=='0'
    assert app.metric[0].value==app.metric[2].value


def test_single_dashboard_interactions():
    app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=90).run()
    assert not app.exception
    assert [tab.label for tab in app.tabs][:4] == ['Vue d’ensemble', 'Explorer les connexions', 'Performance du modèle', 'Vérifier une connexion']
    next(button for button in app.button if button.label == 'Analyser la connexion').click().run()
    assert not app.exception
    next(button for button in app.button if button.label == 'Connexion suspecte').click().run()
    assert not app.exception
    assert len(app.session_state['sim_results']) == 1
    next(button for button in app.button if button.label == 'Réinitialiser').click().run()
    assert not app.exception and not app.session_state['sim_results']

def test_sidebar_filters_update_overview():
    app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=90).run()
    app.slider(key='sidebar_limit').set_value(500).run()
    assert not app.exception
    assert app.metric[0].value == '500'
    app.slider(key='sidebar_percentile').set_value(100).run()
    assert not app.exception
    assert app.info
