from prefect.blocks.system import Secret
import sys
#Secret(value="sk-1234567890").save("strava-access-token", overwrite=True)

secret_block = Secret.load(sys.argv[1])

# Access the stored secret
print(secret_block.get())
