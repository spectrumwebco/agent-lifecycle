// Code generated by informer-gen. DO NOT EDIT.

package v1

import (
	context "context"
	time "time"

	apismanagementv1 "github.com/loft-sh/api/v4/pkg/apis/management/v1"
	versioned "github.com/loft-sh/api/v4/pkg/clientset/versioned"
	internalinterfaces "github.com/loft-sh/api/v4/pkg/informers/externalversions/internalinterfaces"
	managementv1 "github.com/loft-sh/api/v4/pkg/listers/management/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	runtime "k8s.io/apimachinery/pkg/runtime"
	watch "k8s.io/apimachinery/pkg/watch"
	cache "k8s.io/client-go/tools/cache"
)

// SpaceInstanceInformer provides access to a shared informer and lister for
// SpaceInstances.
type SpaceInstanceInformer interface {
	Informer() cache.SharedIndexInformer
	Lister() managementv1.SpaceInstanceLister
}

type spaceInstanceInformer struct {
	factory          internalinterfaces.SharedInformerFactory
	tweakListOptions internalinterfaces.TweakListOptionsFunc
	namespace        string
}

// NewSpaceInstanceInformer constructs a new informer for SpaceInstance type.
// Always prefer using an informer factory to get a shared informer instead of getting an independent
// one. This reduces memory footprint and number of connections to the server.
func NewSpaceInstanceInformer(client versioned.Interface, namespace string, resyncPeriod time.Duration, indexers cache.Indexers) cache.SharedIndexInformer {
	return NewFilteredSpaceInstanceInformer(client, namespace, resyncPeriod, indexers, nil)
}

// NewFilteredSpaceInstanceInformer constructs a new informer for SpaceInstance type.
// Always prefer using an informer factory to get a shared informer instead of getting an independent
// one. This reduces memory footprint and number of connections to the server.
func NewFilteredSpaceInstanceInformer(client versioned.Interface, namespace string, resyncPeriod time.Duration, indexers cache.Indexers, tweakListOptions internalinterfaces.TweakListOptionsFunc) cache.SharedIndexInformer {
	return cache.NewSharedIndexInformer(
		&cache.ListWatch{
			ListFunc: func(options metav1.ListOptions) (runtime.Object, error) {
				if tweakListOptions != nil {
					tweakListOptions(&options)
				}
				return client.ManagementV1().SpaceInstances(namespace).List(context.TODO(), options)
			},
			WatchFunc: func(options metav1.ListOptions) (watch.Interface, error) {
				if tweakListOptions != nil {
					tweakListOptions(&options)
				}
				return client.ManagementV1().SpaceInstances(namespace).Watch(context.TODO(), options)
			},
		},
		&apismanagementv1.SpaceInstance{},
		resyncPeriod,
		indexers,
	)
}

func (f *spaceInstanceInformer) defaultInformer(client versioned.Interface, resyncPeriod time.Duration) cache.SharedIndexInformer {
	return NewFilteredSpaceInstanceInformer(client, f.namespace, resyncPeriod, cache.Indexers{cache.NamespaceIndex: cache.MetaNamespaceIndexFunc}, f.tweakListOptions)
}

func (f *spaceInstanceInformer) Informer() cache.SharedIndexInformer {
	return f.factory.InformerFor(&apismanagementv1.SpaceInstance{}, f.defaultInformer)
}

func (f *spaceInstanceInformer) Lister() managementv1.SpaceInstanceLister {
	return managementv1.NewSpaceInstanceLister(f.Informer().GetIndexer())
}
