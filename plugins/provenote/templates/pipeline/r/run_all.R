#!/usr/bin/env Rscript
# Run every numbered step src/NN_*.R in order; stop at the first failure.
# Usage: Rscript run_all.R   (from the project root)
# Exit codes: 0 all passed, 1 a step failed, 2 no steps found.
root <- normalizePath(".")
log <- function(msg) cat(format(Sys.time(), "%Y-%m-%dT%H:%M:%S"), msg, "\n")
steps <- sort(list.files(file.path(root, "src"), pattern = "^[0-9][0-9]_.*\\.R$", full.names = TRUE))
if (length(steps) == 0) { log("no steps found in src/"); quit(status = 2) }
for (s in steps) {
  log(paste("START", basename(s)))
  ok <- tryCatch({ source(s, local = new.env()); TRUE },
                 error = function(e) { message("error: ", conditionMessage(e)); FALSE })
  if (!ok) { log(paste("FAIL ", basename(s))); quit(status = 1) }
  log(paste("OK   ", basename(s)))
}
log(paste("PASS ", length(steps), "step(s)"))
