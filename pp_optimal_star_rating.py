"""Around what star ratings do you perform the best?"""

import asyncio
from operator import attrgetter
import os
import sys

import matplotlib.pyplot as plt

import aiosu
from fluentpy import _  # Lets us create readable functional pipelines # pyright: ignore [reportAttributeAccessIssue]


def hash_set_deduplicate():
    seen = set()

    def closure(x):
        if x in seen:
            return False
        else:
            seen.add(x)
            return True

    return closure


async def main():
    # Set up our client to fetch data from the website
    if not (client_id := os.environ.get("CLIENT_ID")) or not (
        client_secret := os.environ.get("CLIENT_SECRET")
    ):
        print(
            "This script requires a client ID and secret to access the osu! API.\n"
            "Please go to your [account settings](https://osu.ppy.sh/home/account/edit), create an OAuth application if you don't already have one, and set the `CLIENT_ID` and `CLIENT_SECRET` environment variables with the client ID and secret for your application.\n"
            "NEVER, EVER SHARE YOUR CLIENT SECRET WITH **ANYONE!**"
        )
        sys.exit(1)
    user_id = int(
        os.environ.get("USER_ID")
        or input(
            "This script requires a user ID to fetch scores for.\n"
            "You may set the `USER_ID` environment variable with your user ID, or you may enter it here.\n"
            "Your user ID is the number at the end of the link to your profile page, e.g. the 35859242 in https://osu.ppy.sh/users/35859242.\n"
            "Enter your osu! user ID: "
        )
    )
    app_client = aiosu.v2.Client(
        client_secret=client_secret,
        client_id=client_id,
    )

    # Neat lil data pipeline to get recent and top plays' pp values and map star ratings
    pps, diffs = (
        _(
            (
                *await app_client.get_user_recents(user_id),
                *await app_client.get_user_bests(user_id),
            )
        )
        .map(aiosu.models.Score.model_dump_json)  # Convert models to hashable JSON
        .filter(hash_set_deduplicate())  # Deduplicate scores using a hash set
        .map(aiosu.models.Score.model_validate_json)  # Convert them back
        .filter(attrgetter("pp"))  # Only include scores that have a pp value
        .map(
            lambda x: (x.pp, x.beatmap.difficulty_rating)
        )  # Get the PP and map star rating of each score
        .star_call(zip)  # Convert [(x1, y1), (x2, y2)] -> [(x1, x2), (y1, y2)] for MPL
    )

    # Show our data!
    plt.scatter(x=diffs, y=pps)
    plt.show()

    # And do final cleanup
    await app_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
