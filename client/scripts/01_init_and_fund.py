from common import actor_from_env, ensure_funded, balances

landlord = actor_from_env("LANDLORD_SECRET")
tenant = actor_from_env("TENANT_SECRET")
arbitrator = actor_from_env("ARBITRATOR_SECRET")

for a in (landlord, tenant, arbitrator):
    ensure_funded(a.kp.public_key)

print("Landlord", landlord.kp.public_key, balances(landlord.kp.public_key))
print("Tenant  ", tenant.kp.public_key,   balances(tenant.kp.public_key))
print("Arb     ", arbitrator.kp.public_key, balances(arbitrator.kp.public_key))
