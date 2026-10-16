{{/* Base name, truncated to fit Kubernetes name limits. */}}
{{- define "deskflow.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "deskflow.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else if contains (include "deskflow.name" .) .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "deskflow.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "deskflow.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "deskflow.labels" -}}
helm.sh/chart: {{ include "deskflow.chart" . }}
app.kubernetes.io/part-of: deskflow
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Selector labels for one component: include with (dict "ctx" $ "component" "backend"). */}}
{{- define "deskflow.selectorLabels" -}}
app.kubernetes.io/name: {{ include "deskflow.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{- define "deskflow.image" -}}
{{- $root := .ctx -}}
{{- if $root.Values.image.registry -}}
{{- printf "%s/%s:%s" $root.Values.image.registry .repository $root.Values.image.tag -}}
{{- else -}}
{{- printf "%s:%s" .repository $root.Values.image.tag -}}
{{- end -}}
{{- end }}

{{- define "deskflow.backendHost" -}}
{{ include "deskflow.fullname" . }}-backend
{{- end }}

{{- define "deskflow.postgresHost" -}}
{{ include "deskflow.fullname" . }}-postgres
{{- end }}

{{- define "deskflow.postgresSecret" -}}
{{- if .Values.postgres.existingSecret -}}
{{ .Values.postgres.existingSecret }}
{{- else -}}
{{ include "deskflow.fullname" . }}-postgres
{{- end -}}
{{- end }}
