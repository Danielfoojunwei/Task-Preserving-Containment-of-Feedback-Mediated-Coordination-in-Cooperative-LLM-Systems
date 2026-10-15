"""Render the selected-after-audit sensitivity separately from primary figures."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent


def main():
    path = ROOT / 'partial_validity_sensitivity.json'
    data = json.loads(path.read_text())
    assert data['status'] == 'COMPLETE_POST_HOC_SENSITIVITY'
    carriers = ['policy_label', 'numeric_receipt', 'rejection_status', 'joint_xor']
    labels = ['Policy label', 'Numeric receipt', 'Rejection status', 'Joint XOR']
    fig, (ax, count_ax) = plt.subplots(1, 2, figsize=(13, 5.3), gridspec_kw={'width_ratios': [1.7, 1]})
    for offset, field, label, color in [(-.13, 'frozen_whole_domain', 'Frozen whole-action endpoint', '#275c7d'),
                                       (.13, 'raw_field_only', 'Post hoc raw decoded-bit endpoint', '#ac5129')]:
        rows = [data['registered_form_contrasts_exploratory_endpoint']['mini|'+c][field] for c in carriers]
        means = np.array([r['mean'] for r in rows])
        lo = np.array([r['bootstrap95'][0] for r in rows])
        hi = np.array([r['bootstrap95'][1] for r in rows])
        ax.errorbar(means, np.arange(4)+offset, xerr=np.array([means-lo, hi-means]),
                    fmt='o', color=color, capsize=4, label=label)
    ax.axvline(0, color='gray', linestyle='--', linewidth=1)
    ax.set_yticks(np.arange(4), labels)
    ax.invert_yaxis()
    ax.set_xlabel('Lower-scope guard minus transcript guard: ΔS')
    ax.set_title('Same 32 mini worlds, same sources and outputs', loc='left')
    ax.legend(frameon=False, loc='lower right', fontsize=9)
    ax.grid(axis='x', alpha=.15)
    counts = data['all_records']
    vals = [counts['correct_raw_bits_discarded_by_whole_domain_validation'],
            counts['wrong_raw_bits_discarded_by_whole_domain_validation'],
            counts['whole_domain_invalid']-counts['numeric_bits_discarded_by_whole_domain_validation']]
    bars = count_ax.bar(['Correct raw bit', 'Wrong raw bit', 'Raw abstention'], vals,
                        color=['#ac5129', '#9b7986', '#a5adb2'])
    count_ax.bar_label(bars, padding=4)
    count_ax.set_ylim(0, max(vals)*1.18)
    count_ax.set_ylabel('Receiver records rejected for checksum domain error')
    count_ax.set_title('476 rejected actions: all models and study kinds', loc='left', fontsize=11)
    count_ax.tick_params(axis='x', labelrotation=18)
    fig.suptitle('Post hoc sensitivity: whole-action validity can suppress usable bit predictions',
                 fontsize=15, fontweight='bold', y=1.01)
    fig.text(.01, -.015, 'Selected after the audit. Frozen four-test family remains null. Raw-field p-values are exploratory; no rejected route is an executed attack.',
             fontsize=9, color='#56616b')
    fig.tight_layout()
    out = ROOT / 'figures'
    for extension in ('png', 'pdf'):
        fig.savefig(out / ('posthoc_partial_validity_sensitivity.'+extension), dpi=220, bbox_inches='tight')
    plt.close(fig)
    provenance = {'status': 'POST_HOC_EXPLORATORY', 'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'renderer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'caption': 'Field-wise score sensitivity with 95% public-world bootstrap intervals. Single-carrier comparator is payload_only; joint comparator is marginal_guard. Right panel covers all 1456 receiver records, not only main mini. All source errors and planned worlds are included. Selected after audit; does not change the frozen primary analysis.'}
    (out / 'POSTHOC_FIGURE_PROVENANCE.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print('Rendered separate post hoc validity-sensitivity PNG/PDF.')


if __name__ == '__main__':
    main()
