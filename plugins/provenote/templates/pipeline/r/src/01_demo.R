# Demo step: writes one table to output/tables/. Replace with real steps.
dir.create("output/tables", recursive = TRUE, showWarnings = FALSE)
df <- data.frame(key = c("a", "b", "c"), value = 1:3)
write.csv(df, "output/tables/demo_sum.csv", row.names = FALSE)
cat("wrote demo_sum.csv; total =", sum(df$value), "\n")
