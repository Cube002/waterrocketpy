import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle, Polygon
import matplotlib.transforms as mtransforms

def animate_flight(data, rocket_height=1.0, rocket_width=0.2, cone_height=0.2, initial_water_jet=0.5):
    fig, ax = plt.subplots()
    ax.set_xlim(-1, 1)
    ax.set_ylim(0, np.max(data.altitude) + 2)
    ax.set_aspect('equal')
    ax.set_facecolor('skyblue')
    ax.fill_between([-1, 1], 0, 0.1, color='green')

    rocket_body = Rectangle((-rocket_width / 2, 0), rocket_width, rocket_height, color='gray')
    rocket_cone = Polygon([
        [0, rocket_height],
        [-rocket_width / 2, rocket_height],
        [0, rocket_height + cone_height],
        [rocket_width / 2, rocket_height]
    ], closed=True, color='darkred')
    water_jet, = ax.plot([], [], 'b', lw=4, alpha=0.6)

    ax.add_patch(rocket_body)
    ax.add_patch(rocket_cone)

    # Event annotations: label, altitude, color
    events = [
        ("Max Altitude", data.max_altitude, 'green'),
        ("Max Velocity", data.altitude[np.argmax(np.abs(data.velocity))], 'purple'),
        ("Water Depletion", np.interp(data.water_depletion_time, data.time, data.altitude), 'blue'),
        ("Air Depletion", np.interp(data.air_depletion_time, data.time, data.altitude), 'orange')
    ]
    events = sorted(events, key=lambda x: -x[1])  # Sort descending altitude

    for i, (label, alt, color) in enumerate(events):
        x_arrow = 0.8 if i % 2 == 0 else -0.8
        ha = 'left' if x_arrow > 0 else 'right'
        ax.axhline(y=alt, color=color, linestyle='--', linewidth=1)
        ax.annotate(
            label,
            xy=(0.6, alt),
            xytext=(x_arrow, alt + 0.5),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
            color=color, fontsize=9, ha=ha
        )

    def init():
        rocket_body.set_xy((-rocket_width / 2, 0))
        rocket_cone.set_xy([
            [0, rocket_height],
            [-rocket_width / 2, rocket_height],
            [0, rocket_height + cone_height],
            [rocket_width / 2, rocket_height]
        ])
        water_jet.set_data([], [])
        return rocket_body, rocket_cone, water_jet

    def update(i):
        y = float(data.altitude[i])
        v = data.velocity[i]
        rocket_body.set_xy((-rocket_width / 2, y))
        rocket_cone.set_xy([
            [0, y + rocket_height],
            [-rocket_width / 2, y + rocket_height],
            [0, y + rocket_height + cone_height],
            [rocket_width / 2, y + rocket_height]
        ])

        base_transform = ax.transData
        if v >= 0:
            rocket_body.set_transform(base_transform)
            rocket_cone.set_transform(base_transform)
        else:
            cx, cy = 0, y + rocket_height / 2
            rotate_transform = mtransforms.Affine2D().rotate_deg_around(cx, cy, 180) + base_transform
            rocket_body.set_transform(rotate_transform)
            rocket_cone.set_transform(rotate_transform)

        if data.water_mass[i] > 0:
            jet_len = initial_water_jet * (data.water_mass[i] / np.max(data.water_mass))
            water_jet.set_data([0, 0], [y, y - jet_len])
        else:
            water_jet.set_data([], [])

        return rocket_body, rocket_cone, water_jet

    ani = FuncAnimation(fig, update, frames=len(data.time),
                        init_func=init, blit=True, interval=30)

    plt.title("2D Water Rocket Animation🚀")
    plt.tight_layout()
    plt.show()
