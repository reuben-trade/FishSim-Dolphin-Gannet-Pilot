# Native facade draft — certification remains pending

The notebook's native opt-in uses `certified_native_v1.run`. This small additive
facade retains the installed e37 helper's release validation, argument plan
and execution. It adds a check for the legacy headless analysis launcher's
`.headless/ipython`, `.headless/runtime` and `.headless/share/jupyter`
environment markers. A matching context stops before delegation. The check
does not modify or clear the user's environment.

The modern headless driver is already analysis-only and rejects `RUN_NATIVE`
before kernel startup. The facade also protects the old unchanged launcher,
whose timeout and receipt describe saved analysis. Native replay belongs in a
clean GUI kernel or the separate certified finite CLI.

This draft contains no accepted release certificate or root acceptance hash.
`RUN_NATIVE` stays `False`. No new kernel, model import, constructor, compiler,
lease or integration is run to prepare this source-only guard. The focused
recording-delegate tests verify routing, not successful release validation or
native execution.

After both artifact-specific full-horizon proofs and root acceptance exist,
the pending bindings must be replaced by actual archived proofs. A gate-only
positive and space-path test with model execution denied, plus a fresh default
notebook proof, remain required before publication. Existing code, templates,
paper, data and all historical protected paths remain unchanged.
