export const BUILDINGS = [
  {
    name: "Living habitat",
    asset: "habitat",
    x: -15,
    z: 5,
    halfX: 7.1,
    halfZ: 5.8,
    color: "#e7e1ce",
    description:
      "Your crew’s home. Essential support always uses 4 energy each turn.",
  },
  {
    name: "Life support",
    asset: "life-support",
    x: -17,
    z: -13,
    halfX: 5.1,
    halfZ: 3.1,
    color: "#dfe8df",
    description:
      "Atmosphere processing produces 12 oxygen for 4 energy. The crew consumes 12 oxygen each turn. Water recycling is visual equipment, not an extra game resource.",
  },
  {
    name: "Greenhouse",
    asset: "greenhouse",
    x: 1,
    z: -23,
    halfX: 7.1,
    halfZ: 3.4,
    color: "#91a67b",
    description:
      "Two consecutive powered turns harvest 2 meal packs. Each powered turn costs 3 energy and 1 water. Turning lights off resets crop progress.",
  },
  {
    name: "Science lab",
    asset: "laboratory",
    x: 18,
    z: -12,
    halfX: 6.2,
    halfZ: 4.2,
    color: "#f0dfc1",
    description:
      "Lab research uses 4 energy and completes one research objective. Your crew can perform only one task per turn.",
  },
  {
    name: "Radiation shelter",
    asset: "shelter",
    x: 20,
    z: 10,
    halfX: 5.5,
    halfZ: 5.8,
    color: "#7c8b81",
    description:
      "Sheltering costs your crew task and 2 energy for ventilation. Exposure falls by 75% this turn. Shield upgrades offer permanent protection.",
  },
  {
    name: "Communication center",
    asset: "communications",
    x: -23,
    z: -28,
    halfX: 4.1,
    halfZ: 4.1,
    color: "#e5cda9",
    description:
      "Spend a crew task and 2 energy to ask Earth. A planning hint arrives next turn. Advice is optional.",
  },
  {
    name: "Power station",
    asset: "power",
    x: 18,
    z: -30,
    halfX: 6.2,
    halfZ: 4.2,
    color: "#394b5e",
    description:
      "Solar panels generate 10 energy, or 6 during dust. Battery capacity is 20. Essential base support always costs 4 energy.",
  },
  {
    name: "Storage center",
    asset: "storage",
    x: -17,
    z: 24,
    halfX: 5.2,
    halfZ: 6,
    color: "#c6ac8c",
    description:
      "The crew consumes 1 water and 1 meal pack every turn. The greenhouse and rover use extra water. This mission has no separate repair inventory.",
  },
] as const;
export type BuildingName = (typeof BUILDINGS)[number]["name"];
