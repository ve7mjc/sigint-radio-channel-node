# RTLSDR-Airband Configuration
# Automatically Generated

{% if global_tau %}
tau = {{ global_tau }};
{% endif %}
{% for override in global_overrides %}
{{ override }}
{% endfor %}

devices: (
{% for device in devices %}{
    type = "{{ device.type }}";
    {% if device.device_string %}
    device_string = "{{ device.device_string }}";
    {% endif %}
    {% if device.index %}
    index = {{ device.index }};
    {% endif %}
    {% if device.serial %}
    serial = "{{ device.serial }}";
    {% endif %}
    {% if device.gain %}
    gain = {{ device.gain }};
    {% endif %}
    {% if device.correction %}
    correction = {{ device.correction }};
    {% endif %}
    centerfreq = {{ device.centerfreq }};
    channels: (
    {% for channel in device.channels %}
    {
        freq = {{ '{:.3f}'.format(channel.freq) }};
        {% if channel.modulation %}
        modulation = "{{ channel.modulation }}";
        {% endif %}
        {% if channel.ctcss %}
        ctcss = {{ channel.ctcss }};
        {% endif %}
        {% for override in channel.overrides %}
        {{ override }}
        {% endfor %}
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
