// Stub - Firebase Firestore removed in favour of localStorage
export enum OperationType {
  CREATE = 'CREATE',
  READ = 'READ',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
}

export function handleFirestoreError(error: any, _op: OperationType, _collection: string) {
  console.warn('[Firestore stub]', error);
}
