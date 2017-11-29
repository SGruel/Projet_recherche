import numpy as np
import Traitement.formatage as frm
import matplotlib.pyplot as plt
import time

def moindreCarres_iter(data, periode,t0,a,b,p,pointsFaux,covariance=False):
    """
    Effectue une iteration du traitement par moindre carrés, ajoutant un point faux à la liste si elle existe
    :param data: donnée formatée
    :param periode: période influent sur la série
    :param t0: temps moyen de la série
    :param axe: axe sur lequel on traite les moindres carrés
    :param pointsFaux: liste des point faux
    :param covariance: matrice de covariance optionelle
    :return:
    """





    # on calcul la matrice normale avec un traitement par ligne de meme pour le vecteur constant

    N = np.zeros((len(a[0]), len(a[0])))
    K = np.zeros((len(a[0]), 1))
    for i in range(len(a)):
        if i not in pointsFaux:
            Ni = matriceNormaleLigne(a[i], p[i, i])
            Ki = vecteurKligne(a[i, :], p[i][i], b[i])
            N += Ni
            K += Ki
    # on calcul alors les vecteurs des inconnues ainsi que le vecteur residu
    Ninv=np.linalg.inv(N)
    X = np.dot(Ninv, K)
    V = b - np.dot(a, X)
    East_true = np.dot(a, X)
    # on  regarde ensuite le facteur unitaire
    sigma2 = np.dot(np.transpose(V), np.dot(p, V)) / (
        len(data) - len(a[1]))  # len(a[1]) correspondant au nombre de paramêtre
    # on traite ensuite les points faux
    Vnorm=np.zeros((V.shape[0],V.shape[1]))
    for i in range (len(V)):
        Vnorm[i]=V[i]/np.sqrt(sigma2*(1/p[i][i]-np.dot(a[i],np.dot(Ninv,a[i].reshape((len(a[i]), 1))))))
    err=np.where(Vnorm>3)[0]
    max=-1
    ierr=-1
    for e in err:
        if Vnorm[e]> max and e not  in pointsFaux:
            max=Vnorm[e]
            ierr=e
    if max != -1:
        pointsFaux.append(ierr)




    #on regarde ensuite les autre éléments statistiques
    covX = sigma2 * np.linalg.inv(N)

    # on extrait maintenant le rendu voulu
    res = [sigma2]
    for i in range(len(X)):
        res.append([X[i], np.sqrt(covX[i][i])])

    return [res,pointsFaux]


def matriceB(data, axe):
    """
    creation de la matrice des observations à partir de la donnée formatée, sous forme de colonne (East) ou (North) ou(Up) celon l'axe sur lequel on mesure la vitesse
                                                                                                  
    :param data: jeu de données formaté
    :param axe: axe choisi "East","North" ou "Up"
    
    :return: matrice colonne
    """
    indice = 0
    if axe == "North":
        indice = 3
    elif axe == "East":
        indice = 2
    else:
        indice = 4

    B = np.zeros((len(data), 1))
    B[:, 0] = data[:, indice]
    return B


def matriceA(data, t0, periode):
    """
    creation de la matrice d'estimation des paramètre;
    autant de ligne que d'observation;
    en colonne: ( 1  t-t0  (cosinus des période) alterné avec (sinusoide des périodes) (indice de saut nul si différent  1 sinon)
    
    
    :param data: jeu formaté
    :param periode: liste des périodes  utilisée
    :param t0: temps de reference
    :return: matrice
    """
    liste_saut = []
    for i in range(len(data)):
        if data[i, 0] != 1 and not (data[i, 0] in liste_saut):
            liste_saut.append(int(data[i, 0]))

    nb_serie = len(liste_saut)
    A = np.zeros((len(data), 2 + 2 * len(periode) + nb_serie))
    A[:, 0] = 1
    A[:, 1] = (data[:, 1] - t0)
    for i in range(len(periode)):
        # implementation des coefficient de périodicité
        A[:, (2 * i + 2)] = np.cos((A[:, 1] / periode[i]))
        A[:, (2 * i + 3)] = np.sin((A[:, 1] / periode[i]))
    # indice de saut

    for i in range(len(liste_saut)):
        loc = np.where(data[:, 0] == liste_saut[i])
        A[loc, i + 2 * len(periode) + 2] = 1

    return A


def matriceP(data, axe, covariance=False):
    """
    Creation de la matrice de poids, prend en compte l'ajout d'un matrice de covariance  sinon utilise les écart-types sur le mesure de la donnée formatée
    
    (ne prends pas encore en compte la covariance)8/11
    :param data: jeu de  donnée formaté 
    :param covariance:  matrice  fourni par l'utilisateur , doit etre adaptée au jeu de donnée.
    :param axe: axe choisi "East","North" ou "Up"
    :return: matrice de poids
    
    
    """

    P = np.zeros((len(data), len(data)))
    indice = 0
    if axe == "North":
        indice = 6
    elif axe == "East":
        indice = 5
    else:
        indice = 7
    if covariance == False:
        di = np.diag_indices_from(P)
        P[di] = 1 / data[:, indice] ** 2
    return P


def matriceNormaleLigne(A, P):
    """
    Fonction de sous-calcul de la matrice normale pour le traitement ligne par ligne. effectue le produit AtPA sur une ligne de la matrice A.
    :param A: matrice  A
    :param P: Matrice de poids P
    :return: matrice carrée de la longueur de A
    """
    at = A.reshape((len(A), 1))
    A = A.reshape(1, len(A))
    N = np.dot(at, np.dot(P, A))
    return N


def vecteurKligne(A, P, B):
    """
    Fonction de calcul d'un élément du vecteur K . Le calcul est fait par ligne  de manière  à alleger ce dernier.
    :param A: ligne de la matrice A
    :param P: colonne de la matrice P correspondant  à la ligne de A
    :param B:  observation
    :return: matrice composé d'un élément unique
    """
    at = A.reshape((len(A), 1))

    K = at * P * B
    return K




def moindreCarres(data,periode,covariance=False):
    """
    Renvoie le résultat d'un traitement par moindre carrés d'un jeu de données formaté par la méthode formatage.
    Les parametres d'entrée sont envoyés par la fonction traitement.
    :param data: jeu de données comprenant date série E N U  et écarts type sur ces coordonnées.
    :param covariance: Matrice de covariance supplémentaire dans le cadre de param^tre extérieures  intervnant sur la donnée mesurée
    :param periode: périodes influencant la donnée, celles-ci peuvent etre multiple ( a entrer sous forme de liste)
    :type data: numpy.array
    :type covariance:numpy.array
    :type periode : list
    """
    t0 = np.mean(data[:, 1])
    resultat = [t0]

    # premier traitement avec un axe, on comence par la creation de matrice
    be = matriceB(data,"East")
    # pour la date de référence, on prend cette dernière au milieu du jeu de données
    a = matriceA(data, t0, periode)
    pe = matriceP(data, "East", covariance)


    #on traite  un premier axe une première fois pour initialiser une liste de point faux
    point_faux=moindreCarres_iter(data,periode,t0,a,be,pe,[])[1]
    #on itère jusqu'à ce qu'il n'y ai plus de points faux
    res=0
    for i in point_faux:
        res= moindreCarres_iter(data,periode,t0,a,be,pe,point_faux)[0]
    resultat.append(res)
    #on redéfini les matrices pour les deux autres axes
    bn=matriceB(data,'North')
    bu=matriceB(data,'Up')
    pn=matriceP(data,'North')
    pu=matriceP(data,'Up')
    res=0
    for i in point_faux:
        res= moindreCarres_iter(data,periode,t0,a,bn,pn,point_faux)[0]
    resultat.append(res)
    res=0
    for i in point_faux:
        res= moindreCarres_iter(data,periode,t0,a,bu,pu,point_faux)[0]

    resultat.append(res)
    return resultat


