from app.db import init_db, upsert_influencer, all_influencers

def test_import_and_deduplicate():
    init_db()
    row={"name":"Test Creator","username":"unit_test_creator","niche":"Tech","followers":1000}
    upsert_influencer(row)
    upsert_influencer({**row,"followers":1200})
    matches=[x for x in all_influencers() if x["username"]=="unit_test_creator"]
    assert len(matches)==1
    assert matches[0]["followers"]==1200
