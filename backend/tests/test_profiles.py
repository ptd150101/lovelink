import pytest
from apps.profiles.models import Profile,ProfilePhoto

@pytest.mark.django_db
def test_publish_requires_photo(api_client,user_factory):
 user=user_factory();api_client.force_authenticate(user)
 r=api_client.post("/api/v1/me/profile/publish")
 assert r.status_code==400 and "photos" in r.data

@pytest.mark.django_db
def test_discover_excludes_self_and_hidden(api_client,user_factory):
 a=user_factory("a@example.com",gender=Profile.Gender.MALE,interested_genders=[Profile.Gender.FEMALE])
 b=user_factory("b@example.com",gender=Profile.Gender.FEMALE,interested_genders=[Profile.Gender.MALE])
 b.profile.visibility_status=Profile.Visibility.PUBLISHED;b.profile.save()
 ProfilePhoto.objects.create(profile=b.profile,object_key="profiles/b/1.jpg",public_url="http://example/1.jpg",is_primary=True,mime_type="image/jpeg")
 api_client.force_authenticate(a);r=api_client.get("/api/v1/discover")
 assert r.status_code==200
 ids=[x["public_id"] for x in r.data["results"]]
 assert str(b.profile.public_id) in ids and str(a.profile.public_id) not in ids
