#!/usr/bin/env python3
import json, pathlib

m = pathlib.Path('main.nf').read_text()
m = m.replace(
    '    main:\n',
    '    main:\n\n    // Validate that at least one input source is provided\n    if (!params.input && !params.fetchngs_outdir) {\n        error "Please provide either --input (samplesheet CSV) or --fetchngs_outdir (S3 path to fetchngs output directory)."\n    }\n')
m = m.replace(
    '    ch_samplesheet = channel.value(file(params.input, checkIfExists: true))',
    '    // When triggered by a fetchngs bucket event, discover the samplesheet\n    // from the fetchngs output directory instead of requiring --input.\n    //\n    if (params.fetchngs_outdir) {\n        def samplesheet_path = "${params.fetchngs_outdir}/samplesheet/samplesheet.csv"\n        log.info "Discovering samplesheet from fetchngs output: ${samplesheet_path}"\n        ch_samplesheet = channel.value(file(samplesheet_path, checkIfExists: true))\n    }\n    else {\n        ch_samplesheet = channel.value(file(params.input, checkIfExists: true))\n    }')
pathlib.Path('main.nf').write_text(m)

c = pathlib.Path('nextflow.config').read_text()
c = c.replace("    input                      = null", "    input                      = null\n    fetchngs_outdir            = null  // S3 path to fetchngs output dir; discovers samplesheet automatically")
pathlib.Path('nextflow.config').write_text(c)

s = json.loads(pathlib.Path('nextflow_schema.json').read_text())
defs_key = '$defs' if '$defs' in s else 'definitions'
io = s[defs_key]['input_output_options']
io['required'] = ['outdir']
props = io['properties']
keys = list(props.keys())
idx = keys.index('input') + 1
new_props = {}
for i, k in enumerate(keys):
    new_props[k] = props[k]
    if i + 1 == idx:
        new_props['fetchngs_outdir'] = {'type': 'string', 'description': 'S3 path to a fetchngs output directory. When set, the pipeline discovers the samplesheet at <fetchngs_outdir>/samplesheet/samplesheet.csv automatically, and --input is not required.', 'help_text': 'Use this parameter when triggering nf-core/rnaseq from a Seqera Platform bucket event action that watches for fetchngs completion.', 'format': 'directory-path', 'fa_icon': 'fas fa-folder-open'}
io['properties'] = new_props
pathlib.Path('nextflow_schema.json').write_text(json.dumps(s, indent=4) + '\n')
print("All 3 files patched.")
