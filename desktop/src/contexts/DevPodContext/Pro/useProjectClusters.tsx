import { useProContext } from "@/contexts"
import { QueryKeys } from "@/queryKeys"
import { ManagementV1Runner } from "@/runner"
import { ManagementV1ProjectClusters } from "../api/v1/management_v1_typesProjectClusters"
import { useQuery, UseQueryResult } from "@tanstack/react-query"

type TProjectCluster = ManagementV1ProjectClusters & {
  runners?: Array<ManagementV1Runner>
}
export function useProjectClusters(): UseQueryResult<TProjectCluster | undefined> {
  const { host, currentProject, client } = useProContext()
  const query = useQuery({
    queryKey: QueryKeys.proClusters(host, currentProject?.metadata!.name!),
    queryFn: async () => {
      return (await client.getProjectClusters(currentProject?.metadata!.name!)).unwrap()
    },
    enabled: !!currentProject,
  })

  return query
}
