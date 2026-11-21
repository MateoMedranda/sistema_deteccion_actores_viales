import type { DetectionResponse, VehicleResult } from "../../services/apiTypes";
export function joinResults(source: DetectionResponse, items: VehicleResult[]) {
  const results: Record<number, VehicleResult> = {};
  for (const result of items) {
    const detection = source.detections.find(
      (d) => d.detection_id === result.detection_id,
    );
    if (
      !detection ||
      !detection.enrichment_eligible ||
      detection.class_id !== result.class_id ||
      detection.class_name !== result.class_name ||
      results[result.detection_id] ||
      result.track_id != null
    )
      throw new Error("invalid_association");
    results[result.detection_id] = result;
  }
  return results;
}
export const classLabel = (name: string) =>
  ({
    car: "Automóvil",
    truck: "Camión",
    bus: "Autobús",
    motorcycle: "Motocicleta",
    person: "Persona",
    bicycle: "Bicicleta",
  })[name] ?? name;
