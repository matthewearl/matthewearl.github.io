
from numpy import *
from matplotlib import pyplot as plt

def show_dac(states, target_v, period, time_constant, fig_name):

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    # Setup the axes.
    ax.set_xticks(arange(0, len(states) + 1, period))
    ax.set_yticks(arange(0, 1.1, 0.1))
    ax.set_xticks(arange(0, len(states) + 1), minor=True)
    ax.grid(which='major', axis='y')
    ax.grid(which='major', axis='x')
    ax.grid(which='minor', axis='x')
    ax.set_ylim(bottom=-0.1, top=1.1)
    
    # Plot the target voltage.
    x_data = [0, len(states)]
    y_data = [target_v, target_v]
    ax.plot(x_data, y_data)

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
    ax.plot(x_data, y_data, linewidth=1)

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
    ax.plot(x_data, y_data, linewidth=1)

    # Show the graph.
    plt.savefig("{}.svg".format(fig_name))
    plt.show()

def show_line(states, N, D):
    # Setup the axes
    plt.xlim(0, D)
    plt.xlabel("time")
    plt.ylabel("output sum")

    # Plot the line.
    x_data = [0, D]
    y_data = [0, N]
    plt.plot(x_data, y_data)

    # Plot the approximation.
    x_data = []
    y_data = []
    x, y = 0, 0
    prev_y = None
    for state in states:
        prev_y = y
        if state:
            y += 1

        if prev_y is None or prev_y != y:
            x_data.append(x)
            y_data.append(prev_y)
            x_data.append(x)
            y_data.append(y)

        x += 1
    plt.plot(x_data, y_data)

    # Show the graph.
    plt.savefig("bresenham.svg")
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

show_line(list(pwm6(20, 32)),
          20, 32) 

