# RTLSDR-Airband Configuration
# Automatically Generated

devices: (
{% for device in devices %}{
    type = "{{ device.type }}";
    index = {{ device.index }};
    {% if device.gain %}
    gain = {{ device.gain }};
    {% endif %}
    {% if device.ppm_correction %}
    correction = {{ device.ppm_correction }};
    {% endif %}
    centerfreq = {{ device.centerfreq }};
    channels: (
    {% for channel in device.channels %}
    {
        name = "{{ channel.name }}";
        freq = {{ channel.freq }};
        {% if channel.modulation %}
        modulation = "{{ channel.modulation }}";
        {% endif %}
        {% if channel.ctcss %}
        ctcss = {{ channel.ctcss }};
        {% endif %}
        outputs: (
        {% for output in channel.outputs %}
        {
            {% for key, value in output.items() %}
            {{ key }} = {{ value }};
            {% endfor %}
        }{{ "," if not loop.last }}
        {% endfor %}
        );
    }{{ "," if not loop.last }}
    {% endfor %}
    );
}{{ "," if not loop.last }}
{% endfor %}
);
