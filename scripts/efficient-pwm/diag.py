
from numpy import *
from matplotlib import pyplot as plt

def show_dac(states, target_v, period, time_constant, fig_name):

    # Setup the axes.
    plt.xticks(arange(0, len(states) + 1, period))
    plt.yticks(arange(0, 1.1, 0.1))
    plt.grid(True)
    
    # Plot the target voltage.
    x_data = [0, len(states)]
    y_data = [target_v, target_v]
    plt.plot(x_data, y_data)

    # Plot the raw pin-out.
    x_data = []
    y_data = []
    prev_state = None
    for x, state in enumerate(states):
        if prev_state != state:
            if prev_state is not None:
                x_data.append(x)
                y_data.append(int(prev_state))
            x_data.append(x)
            y_data.append(int(state))
        prev_state = state
    x_data.append(len(states))
    y_data.append(int(prev_state))
    plt.plot(x_data, y_data, linewidth=1)

    # Plot the RC filtered data.
    x_data = []
    y_data = []
    v = 0.0
    for i, state in enumerate(states):
        v0 = float(state) - v
        for j in arange(0, 1., 0.01):
            v = float(state) - v0 * math.exp(-j / time_constant)
            t = float(i) + j

            x_data.append(t)
            y_data.append(v)
    plt.plot(x_data, y_data, linewidth=1)

    # Show the graph.
    plt.savefig("{}.svg".format(fig_name))
    plt.show()

show_dac(([True] * 20 + [False] * 12) * 4,
         20. / 32,
         32,
         16,
         "naive")


def pwm6(N, D):
    h2 = N
    for i in range(D):
        if h2 < N:
            h2 += (D - N)
            yield True
        else:
            h2 -= N
            yield False

show_dac(list(pwm6(20, 32)) * 4,
         20. / 32,
         32,
         16,
         "efficient")



