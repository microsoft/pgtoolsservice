{#
 # Copyright (c) Microsoft Corporation. All rights reserved.
 # Licensed under the MIT License. See License.txt in the project root for license information.
 #}
select {% if data.columns and data.columns|length > 0 %} {% for c in data.columns %}{% if c.name %}{% if loop.index != 1 %}{{'\n,'}}{% endif %}{{conn|qtIdent(c.name)}}{% endif %}{% endfor %}{% endif %}
from {{conn|qtIdent(data.schema, data.name)}}
LIMIT 1000
