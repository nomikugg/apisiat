import pytest

from app.integrations.siat.exceptions import SiatConnectionError
from app.integrations.siat.soap_client import SiatAuthClient, SiatSoapClient, _build_transport


def test_build_transport_sin_token_no_agrega_header_authorization():
    transport = _build_transport(None)
    assert "Authorization" not in transport.session.headers


def test_build_transport_con_token_agrega_header_authorization_token():
    transport = _build_transport("ABC123")
    assert transport.session.headers["Authorization"] == "Token ABC123"


def test_soap_client_sin_wsdl_configurado_levanta_siat_connection_error():
    with pytest.raises(SiatConnectionError):
        SiatSoapClient(wsdl_url="")


def test_auth_client_sin_wsdl_configurado_levanta_siat_connection_error():
    with pytest.raises(SiatConnectionError):
        SiatAuthClient(wsdl_url="")
