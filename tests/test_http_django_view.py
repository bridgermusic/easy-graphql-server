def test_http_response(app_client):
    response = app_client.get("/api/v1")
    assert response.status_code == 400
    # django application is well integrated
