from app.schemas import CategoryReconciliation, PLASTIC_CATEGORIES, StoredDeclaration


def reconcile_declaration(
    declaration: StoredDeclaration,
    procured_by_category: dict[str, float],
    tolerance_percent: float = 5.0,
) -> list[CategoryReconciliation]:
    results: list[CategoryReconciliation] = []
    for category in sorted(PLASTIC_CATEGORIES):
        declared = float(declaration.declared_quantities_kg[category])
        procured = float(procured_by_category.get(category, 0.0))
        difference = declared - procured
        if procured == 0:
            difference_percent = None
            flagged = declared != 0
        else:
            difference_percent = (difference / procured) * 100
            flagged = abs(difference_percent) > tolerance_percent

        if flagged and difference > 0:
            status = "over_declared"
        elif flagged and difference < 0:
            status = "under_declared"
        else:
            status = "within_tolerance"

        results.append(
            CategoryReconciliation(
                category=category,
                declared_kg=declared,
                procured_kg=procured,
                difference_kg=round(difference, 2),
                difference_percent=(
                    None if difference_percent is None else round(difference_percent, 2)
                ),
                flagged=flagged,
                status=status,
            )
        )
    return results
