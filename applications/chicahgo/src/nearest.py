#bus stop
node["public_transport"="platform"]["bus"="yes"]

#train station
nwr["public_transport"="station"]["train"="yes"]({{bbox}});

#bakery
nwr["shop"="bakery"]({{bbox}});

# Soul Cycle

class Nearest:
    def __init__(self):
